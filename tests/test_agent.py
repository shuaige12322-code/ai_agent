"""Unit tests for the refactored memory, retrieval, and agent layers."""
import tempfile
from pathlib import Path

import pytest

from app.agent.agent import Agent
from app.memory.memory_manager import MemoryManager, MemoryType
from app.rag.retriever import FakeEmbeddingProvider, RAGRetriever, VectorStore


class TestMemoryManager:
    @pytest.fixture
    def memory_manager(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_memories.db"
            manager = MemoryManager(db_path=str(db_path))
            yield manager

    def test_create_memory(self, memory_manager):
        memory = memory_manager.create_memory(
            user_id="test_user",
            memory_type=MemoryType.USER_PROFILE,
            content="Test memory content",
        )
        assert memory is not None
        assert memory.user_id == "test_user"
        assert memory.memory_type == MemoryType.USER_PROFILE
        assert memory.content == "Test memory content"

    def test_get_user_memories(self, memory_manager):
        memory_manager.create_memory(
            user_id="test_user",
            memory_type=MemoryType.USER_PROFILE,
            content="Profile 1",
        )
        memory_manager.create_memory(
            user_id="test_user",
            memory_type=MemoryType.USER_PREFERENCES,
            content="Preference 1",
        )
        memories = memory_manager.get_user_memories(user_id="test_user")
        assert len(memories) == 2

    def test_search_memories(self, memory_manager):
        memory_manager.create_memory(
            user_id="test_user",
            memory_type=MemoryType.USER_PROFILE,
            content="Python developer from Shanghai",
        )
        memory_manager.create_memory(
            user_id="test_user",
            memory_type=MemoryType.USER_PREFERENCES,
            content="Prefers concise FastAPI examples",
        )
        results = memory_manager.search_memories(user_id="test_user", query="Python")
        assert len(results) > 0
        assert "Python" in results[0].content

    def test_create_or_update_memory_deduplicates(self, memory_manager):
        memory_manager.create_or_update_memory(
            user_id="test_user",
            memory_type=MemoryType.USER_PREFERENCES,
            content="User prefers short code examples",
        )
        memory_manager.create_or_update_memory(
            user_id="test_user",
            memory_type=MemoryType.USER_PREFERENCES,
            content="User prefers short code examples",
        )
        memories = memory_manager.get_user_memories(
            user_id="test_user",
            memory_type=MemoryType.USER_PREFERENCES,
            limit=10,
        )
        assert len(memories) == 1


class TestRAGRetriever:
    @pytest.fixture
    def rag_retriever(self):
        retriever = RAGRetriever(
            vector_store=VectorStore(
                qdrant_path=":memory:",
                collection_name="test_chunks",
                embedding_provider=FakeEmbeddingProvider(dimension=48),
            )
        )
        yield retriever
        retriever.vector_store.close()

    def test_add_documents(self, rag_retriever):
        documents = [
            "Python is a programming language",
            "FastAPI is a web framework",
        ]
        doc_ids = rag_retriever.add_knowledge_base(documents)
        assert len(doc_ids) == 2

    def test_retrieve_documents(self, rag_retriever):
        documents = [
            "Python is a high-level programming language",
            "FastAPI is a modern web framework for Python",
            "Machine learning is a subset of AI",
        ]
        rag_retriever.add_knowledge_base(documents)
        results = rag_retriever.retrieve(query="Python programming")
        assert len(results) > 0
        assert any("Python" in result["content"] for result in results)


class TestAgent:
    @pytest.fixture
    def agent(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            memory_db = Path(tmpdir) / "memory.db"
            agent = Agent(
                user_id="test_user",
                memory_manager=MemoryManager(db_path=str(memory_db)),
                rag_retriever=RAGRetriever(
                    vector_store=VectorStore(
                        qdrant_path=":memory:",
                        collection_name="agent_test_chunks",
                        embedding_provider=FakeEmbeddingProvider(dimension=48),
                    )
                ),
            )
            yield agent
            agent.rag_retriever.vector_store.close()

    def test_agent_initialization(self, agent):
        assert agent.user_id == "test_user"
        assert agent.memory_manager is not None
        assert agent.rag_retriever is not None

    def test_add_to_memory(self, agent):
        agent.add_to_memory(
            memory_type=MemoryType.USER_PROFILE,
            content="Test profile",
        )
        memories = agent.get_user_memories()
        assert len(memories) > 0

    def test_add_knowledge_documents(self, agent):
        documents = ["Document 1", "Document 2"]
        doc_ids = agent.add_knowledge_documents(documents)
        assert len(doc_ids) == 2

    def test_clear_conversation(self, agent):
        agent.clear_conversation()
        assert len(agent.get_conversation_history()) == 0

    def test_message_analysis_persists_preference(self, agent):
        state = agent._analyze_user_message("I prefer concise Python examples")
        agent._persist_extracted_memories(state["extracted_memories"])
        memories = agent.get_user_memories(memory_type=MemoryType.USER_PREFERENCES)
        assert len(memories) >= 1

    def test_stream_chat_persists_assistant_reply(self, agent, monkeypatch):
        def fake_stream(system_prompt):
            assert "Say hi" in system_prompt
            yield "Hello"
            yield " there"

        monkeypatch.setattr(agent, "_generate_response_stream", fake_stream)

        chunks = list(agent.stream_chat("Say hi", use_rag=False, retrieve_k=1))

        assert chunks == ["Hello", " there"]
        history = agent.get_conversation_history()
        assert history[-2]["role"] == "user"
        assert history[-2]["content"] == "Say hi"
        assert history[-1]["role"] == "assistant"
        assert history[-1]["content"] == "Hello there"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
