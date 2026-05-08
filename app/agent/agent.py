"""
Agent核心模块
集成了记忆系统、RAG和Claude API
"""
import logging
from typing import List, Dict, Any, Optional
import anthropic
from app.config.config import get_config
from app.memory.memory_manager import MemoryManager, MemoryType
from app.rag.retriever import RAGRetriever

logger = logging.getLogger(__name__)
config = get_config()


class ConversationMessage:
    """对话消息"""
    
    def __init__(self, role: str, content: str):
        self.role = role  # "user" or "assistant"
        self.content = content
    
    def to_dict(self) -> Dict[str, str]:
        """转换为字典"""
        return {"role": self.role, "content": self.content}


class Agent:
    """
    AI Agent - 集成记忆系统、RAG和Claude API
    
    核心特性：
    1. 使用Claude的Memories API管理用户记忆（而非通过历史上下文）
    2. 集成RAG系统用于增强生成
    3. 保持独立的对话上下文
    """
    
    def __init__(self, user_id: str):
        """
        初始化Agent
        
        Args:
            user_id: 用户ID
        """
        self.user_id = user_id
        self.client = anthropic.Anthropic(api_key=config.CLAUDE_API_KEY)
        self.memory_manager = MemoryManager()
        self.rag_retriever = RAGRetriever()
        self.conversation_history: List[ConversationMessage] = []
        
        # 初始化用户记忆
        self._init_user_memories()
    
    def _init_user_memories(self) -> None:
        """初始化用户记忆"""
        existing_memories = self.memory_manager.get_user_memories(
            self.user_id,
            memory_type=MemoryType.USER_PROFILE,
            limit=1,
        )
        
        if not existing_memories:
            # 创建初始用户档案
            self.memory_manager.create_memory(
                user_id=self.user_id,
                memory_type=MemoryType.USER_PROFILE,
                content="New user profile created",
                metadata={"initialized": True},
            )
    
    def _get_system_prompt(self) -> str:
        """
        生成系统提示
        包含用户记忆信息和RAG上下文
        """
        # 获取用户记忆
        user_memories = self.memory_manager.get_user_memories(
            self.user_id,
            limit=config.MAX_MEMORIES,
        )
        
        memory_context = ""
        if user_memories:
            memory_context = "\n### User Memory Information:\n"
            for memory in user_memories:
                memory_context += f"- {memory.memory_type}: {memory.content}\n"
        
        system_prompt = """You are a helpful AI assistant with the ability to remember user information and retrieve relevant documents.

Key responsibilities:
1. Maintain coherent conversations
2. Use user memory to personalize responses
3. Reference relevant documents from the knowledge base when appropriate
4. Update user memory based on new information learned

Important: Never mention the memory system or technical implementation details to the user.
Focus on providing helpful, natural responses.
"""
        
        if memory_context:
            system_prompt += memory_context
        
        return system_prompt
    
    def _extract_and_store_memory(self, response: str) -> None:
        """
        从响应中提取并存储新的记忆
        
        Args:
            response: 模型的响应
        """
        # 这里可以实现更复杂的记忆提取逻辑
        # 简单实现：如果对话包含特定关键字，就创建记忆
        
        key_phrases = [
            "remember",
            "i learned",
            "you told me",
            "my preference",
            "my background",
        ]
        
        response_lower = response.lower()
        if any(phrase in response_lower for phrase in key_phrases):
            # 可以创建对话总结记忆
            if len(self.conversation_history) % 5 == 0:  # 每5条消息创建一个总结
                self.memory_manager.create_memory(
                    user_id=self.user_id,
                    memory_type=MemoryType.CONVERSATION_SUMMARY,
                    content=f"Recent conversation update",
                    metadata={"message_count": len(self.conversation_history)},
                )
    
    def chat(
        self,
        user_message: str,
        use_rag: bool = True,
        retrieve_k: int = 3,
    ) -> str:
        """
        用户与Agent的对话
        
        Args:
            user_message: 用户输入
            use_rag: 是否使用RAG
            retrieve_k: RAG检索文档数
            
        Returns:
            Agent的响应
        """
        # 添加用户消息到历史
        self.conversation_history.append(
            ConversationMessage(role="user", content=user_message)
        )
        
        # 构建消息列表
        messages = [msg.to_dict() for msg in self.conversation_history]
        
        # 获取系统提示
        system_prompt = self._get_system_prompt()
        
        # 如果使用RAG，添加检索结果到系统提示
        if use_rag and config.RAG_ENABLED:
            rag_context = self.rag_retriever.build_context(
                user_message,
                k=retrieve_k,
            )
            system_prompt += f"\n\n### Knowledge Base Context:\n{rag_context}"
        
        # 调用Claude API
        logger.info(f"Sending message from user {self.user_id}")
        
        try:
            response = self.client.messages.create(
                model=config.CLAUDE_MODEL,
                max_tokens=config.MAX_TOKENS,
                temperature=config.TEMPERATURE,
                top_p=config.TOP_P,
                system=system_prompt,
                messages=messages,
            )
            
            # 获取响应内容
            assistant_message = response.content[0].text
            
            # 添加助手响应到历史
            self.conversation_history.append(
                ConversationMessage(role="assistant", content=assistant_message)
            )
            
            # 从响应中提取并存储记忆
            self._extract_and_store_memory(assistant_message)
            
            logger.info(f"Response generated for user {self.user_id}")
            
            return assistant_message
            
        except anthropic.APIError as e:
            logger.error(f"API error: {e}")
            raise
    
    def add_to_memory(
        self,
        memory_type: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        显式添加信息到用户记忆
        
        Args:
            memory_type: 记忆类型
            content: 记忆内容
            metadata: 元数据
        """
        self.memory_manager.create_memory(
            user_id=self.user_id,
            memory_type=memory_type,
            content=content,
            metadata=metadata,
        )
    
    def get_user_memories(
        self,
        memory_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        获取用户的记忆
        
        Args:
            memory_type: 记忆类型（可选）
            
        Returns:
            记忆列表
        """
        memories = self.memory_manager.get_user_memories(
            self.user_id,
            memory_type=memory_type,
            limit=config.MAX_MEMORIES,
        )
        
        return [memory.to_dict() for memory in memories]
    
    def add_knowledge_documents(
        self,
        documents: List[str],
        metadata_list: Optional[List[Dict[str, Any]]] = None,
    ) -> List[str]:
        """
        添加知识库文档
        
        Args:
            documents: 文档列表
            metadata_list: 元数据列表
            
        Returns:
            添加的文档ID列表
        """
        doc_ids = self.rag_retriever.add_knowledge_base(
            documents=documents,
            metadata_list=metadata_list,
        )
        
        logger.info(f"Added {len(doc_ids)} documents to knowledge base")
        return doc_ids
    
    def clear_conversation(self) -> None:
        """清除对话历史"""
        self.conversation_history = []
        logger.info(f"Cleared conversation history for user {self.user_id}")
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """获取对话历史"""
        return [msg.to_dict() for msg in self.conversation_history]
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """获取用户的记忆统计"""
        return self.memory_manager.get_memory_stats(self.user_id)
