"""
Agent orchestration built around explicit state transitions.

The flow now resembles a LangGraph-style pipeline:
analyze input -> retrieve memory -> retrieve knowledge -> build prompt
-> call model -> persist memories.
"""
import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, Generator, List, Optional

import anthropic

from app.config.config import get_config
from app.memory.memory_manager import MemoryManager, MemoryType
from app.rag.retriever import RAGRetriever

logger = logging.getLogger(__name__)
config = get_config()


@dataclass
class ConversationMessage:
    role: str
    content: str

    def to_dict(self) -> Dict[str, str]:
        return {"role": self.role, "content": self.content}


class Agent:
    """Stateful agent with layered memory and RAG-aware orchestration."""

    def __init__(
        self,
        user_id: str,
        memory_manager: Optional[MemoryManager] = None,
        rag_retriever: Optional[RAGRetriever] = None,
    ):
        self.user_id = user_id
        self.client = (
            anthropic.Anthropic(api_key=config.CLAUDE_API_KEY)
            if config.CLAUDE_API_KEY
            else None
        )
        self.memory_manager = memory_manager or MemoryManager()
        self.rag_retriever = rag_retriever or RAGRetriever()
        self.conversation_history: List[ConversationMessage] = []
        self._init_user_memories()

    def _init_user_memories(self) -> None:
        existing = self.memory_manager.get_user_memories(
            self.user_id,
            memory_type=MemoryType.USER_PROFILE,
            limit=1,
        )
        if not existing:
            self.memory_manager.create_memory(
                user_id=self.user_id,
                memory_type=MemoryType.USER_PROFILE,
                content="User profile initialized.",
                metadata={"initialized": True},
                importance=0.2,
                confidence=1.0,
            )

    def _analyze_user_message(self, user_message: str) -> Dict[str, Any]:
        lowered = user_message.lower()
        extracted_memories: List[Dict[str, Any]] = []

        rules = [
            (
                MemoryType.USER_PREFERENCES,
                [
                    r"(?:i prefer|i like|i love)\s+(.+)",
                    r"(?:please use)\s+(.+)",
                    r"(?:我喜欢|我更喜欢|偏好)(.+)",
                    r"(?:请用)(.+)",
                ],
                0.75,
                ["preference"],
            ),
            (
                MemoryType.USER_PROFILE,
                [
                    r"(?:i am|i'm|my role is)\s+(.+)",
                    r"(?:my name is|call me)\s+(.+)",
                    r"(?:我是|我是一名|我的工作是)(.+)",
                    r"(?:我叫)(.+)",
                ],
                0.85,
                ["profile"],
            ),
            (
                MemoryType.TASK_CONTEXT,
                [
                    r"(?:my project|our project)\s+(.+)",
                    r"(?:i am working on)\s+(.+)",
                    r"(?:当前项目|这个项目|项目里)(.+)",
                    r"(?:我正在做)(.+)",
                ],
                0.7,
                ["project"],
            ),
        ]

        for memory_type, patterns, confidence, tags in rules:
            for pattern in patterns:
                match = re.search(pattern, user_message, re.IGNORECASE)
                if match:
                    content = match.group(0).strip().rstrip("。.!?,，")
                    extracted_memories.append(
                        {
                            "memory_type": memory_type,
                            "content": content,
                            "importance": (
                                0.7 if memory_type != MemoryType.TASK_CONTEXT else 0.65
                            ),
                            "confidence": confidence,
                            "tags": tags,
                            "metadata": {"extracted_from": "user_message"},
                        }
                    )

        intent = "question"
        if any(keyword in lowered for keyword in ["fix", "修改", "重构", "optimize", "优化"]):
            intent = "implementation"
        elif any(keyword in lowered for keyword in ["what", "how", "为什么", "适合"]):
            intent = "analysis"

        return {"intent": intent, "extracted_memories": extracted_memories}

    def _get_short_term_context(self) -> str:
        if not self.conversation_history:
            return "No short-term conversation context."

        recent_messages = self.conversation_history[-config.MAX_SHORT_TERM_MESSAGES :]
        lines = ["Recent conversation:"]
        for message in recent_messages:
            lines.append(f"- {message.role}: {message.content[:300]}")
        return "\n".join(lines)

    def _get_memory_context(self, user_message: str) -> str:
        return self.memory_manager.build_memory_context(
            user_id=self.user_id,
            query=user_message,
            limit=config.MAX_MEMORIES,
        )

    def _get_knowledge_context(self, user_message: str, use_rag: bool, retrieve_k: int) -> str:
        if not use_rag or not config.RAG_ENABLED:
            return "Knowledge retrieval disabled for this turn."
        return self.rag_retriever.build_context(user_message, k=retrieve_k)

    def _build_system_prompt(
        self,
        user_message: str,
        intent: str,
        memory_context: str,
        knowledge_context: str,
    ) -> str:
        return f"""You are a helpful AI engineering assistant.

Operating mode:
- Keep answers accurate, practical, and implementation-focused.
- Use durable user memory when it improves personalization.
- Use knowledge-base context when it is relevant.
- If memory and retrieved knowledge conflict, prefer the more specific and recent information.
- Never mention internal memory or retrieval implementation unless explicitly asked.

Current intent: {intent}

{self._get_short_term_context()}

{memory_context}

{knowledge_context}

Current user message:
{user_message}
"""

    def _persist_extracted_memories(self, extracted_memories: List[Dict[str, Any]]) -> None:
        for item in extracted_memories:
            self.memory_manager.create_or_update_memory(
                user_id=self.user_id,
                memory_type=item["memory_type"],
                content=item["content"],
                metadata=item.get("metadata"),
                importance=item.get("importance", 0.6),
                confidence=item.get("confidence", 0.7),
                tags=item.get("tags"),
            )

    def _persist_turn_summary(self) -> None:
        recent_messages = self.conversation_history[-config.SUMMARIZE_EVERY_N_MESSAGES :]
        if len(recent_messages) < config.SUMMARIZE_EVERY_N_MESSAGES:
            return

        summary_text = " | ".join(
            f"{message.role}: {message.content[:120]}" for message in recent_messages
        )
        self.memory_manager.create_or_update_memory(
            user_id=self.user_id,
            memory_type=MemoryType.CONVERSATION_SUMMARY,
            content=summary_text,
            metadata={"message_count": len(self.conversation_history)},
            importance=0.45,
            confidence=0.55,
            tags=["summary"],
        )

    def _persist_interaction_memory(self, user_message: str, assistant_message: str) -> None:
        self.memory_manager.create_memory(
            user_id=self.user_id,
            memory_type=MemoryType.INTERACTION_HISTORY,
            content=f"user={user_message}\nassistant={assistant_message[:400]}",
            metadata={"turn_length": len(user_message) + len(assistant_message)},
            importance=0.15,
            confidence=1.0,
            tags=["interaction"],
        )

    def _generate_response(self, system_prompt: str) -> str:
        if self.client is None:
            raise RuntimeError("CLAUDE_API_KEY is not configured.")

        response = self.client.messages.create(
            model=config.CLAUDE_MODEL,
            max_tokens=config.MAX_TOKENS,
            temperature=config.TEMPERATURE,
            top_p=config.TOP_P,
            system=system_prompt,
            messages=[message.to_dict() for message in self.conversation_history],
        )
        return response.content[0].text

    def _generate_response_stream(self, system_prompt: str) -> Generator[str, None, None]:
        if self.client is None:
            raise RuntimeError("CLAUDE_API_KEY is not configured.")

        with self.client.messages.stream(
            model=config.CLAUDE_MODEL,
            max_tokens=config.MAX_TOKENS,
            temperature=config.TEMPERATURE,
            top_p=config.TOP_P,
            system=system_prompt,
            messages=[message.to_dict() for message in self.conversation_history],
        ) as stream:
            for text in stream.text_stream:
                if text:
                    yield text

    def _prepare_turn(
        self, user_message: str, use_rag: bool, retrieve_k: int
    ) -> Dict[str, Any]:
        state = self._analyze_user_message(user_message)
        self.conversation_history.append(ConversationMessage(role="user", content=user_message))
        self._persist_extracted_memories(state["extracted_memories"])

        memory_context = self._get_memory_context(user_message)
        knowledge_context = self._get_knowledge_context(user_message, use_rag, retrieve_k)
        system_prompt = self._build_system_prompt(
            user_message=user_message,
            intent=state["intent"],
            memory_context=memory_context,
            knowledge_context=knowledge_context,
        )
        return {"state": state, "system_prompt": system_prompt}

    def _finalize_turn(self, user_message: str, assistant_message: str) -> None:
        self.conversation_history.append(
            ConversationMessage(role="assistant", content=assistant_message)
        )
        self._persist_interaction_memory(user_message, assistant_message)
        self._persist_turn_summary()
        self.memory_manager.cleanup_expired_memories()

    def chat(self, user_message: str, use_rag: bool = True, retrieve_k: int = 3) -> str:
        prepared = self._prepare_turn(user_message, use_rag, retrieve_k)
        logger.info("Generating response for user %s", self.user_id)
        assistant_message = self._generate_response(prepared["system_prompt"])
        self._finalize_turn(user_message, assistant_message)
        return assistant_message

    def stream_chat(
        self, user_message: str, use_rag: bool = True, retrieve_k: int = 3
    ) -> Generator[str, None, None]:
        prepared = self._prepare_turn(user_message, use_rag, retrieve_k)
        logger.info("Streaming response for user %s", self.user_id)

        chunks: List[str] = []
        for chunk in self._generate_response_stream(prepared["system_prompt"]):
            chunks.append(chunk)
            yield chunk

        assistant_message = "".join(chunks)
        self._finalize_turn(user_message, assistant_message)

    def add_to_memory(
        self,
        memory_type: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.memory_manager.create_or_update_memory(
            user_id=self.user_id,
            memory_type=memory_type,
            content=content,
            metadata=metadata,
            importance=0.7,
            confidence=0.95,
        )

    def get_user_memories(self, memory_type: Optional[str] = None) -> List[Dict[str, Any]]:
        memories = self.memory_manager.get_user_memories(
            user_id=self.user_id,
            memory_type=memory_type,
            limit=config.MAX_MEMORIES,
        )
        return [memory.to_dict() for memory in memories]

    def add_knowledge_documents(
        self,
        documents: List[str],
        metadata_list: Optional[List[Dict[str, Any]]] = None,
    ) -> List[str]:
        return self.rag_retriever.add_knowledge_base(
            documents=documents,
            metadata_list=metadata_list,
        )

    def clear_conversation(self) -> None:
        self.conversation_history = []

    def get_conversation_history(self) -> List[Dict[str, str]]:
        return [message.to_dict() for message in self.conversation_history]

    def get_memory_stats(self) -> Dict[str, Any]:
        return self.memory_manager.get_memory_stats(self.user_id)
