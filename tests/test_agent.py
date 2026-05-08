"""
单元测试 - Agent模块测试
"""
import pytest
import tempfile
from pathlib import Path
from app.agent.agent import Agent
from app.memory.memory_manager import MemoryManager, MemoryType
from app.rag.retriever import RAGRetriever, Document


class TestMemoryManager:
    """记忆管理器测试"""
    
    @pytest.fixture
    def memory_manager(self):
        """创建临时内存管理器"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_memories.db"
            manager = MemoryManager(db_path=str(db_path))
            yield manager
    
    def test_create_memory(self, memory_manager):
        """测试创建记忆"""
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
        """测试获取用户记忆"""
        # 创建多个记忆
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
        """测试搜索记忆"""
        memory_manager.create_memory(
            user_id="test_user",
            memory_type=MemoryType.USER_PROFILE,
            content="Python developer from Shanghai",
        )
        
        results = memory_manager.search_memories(
            user_id="test_user",
            query="Python",
        )
        assert len(results) > 0
        assert "Python" in results[0].content


class TestRAGRetriever:
    """RAG检索器测试"""
    
    @pytest.fixture
    def rag_retriever(self):
        """创建临时RAG检索器"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_vectors.db"
            retriever = RAGRetriever()
            retriever.vector_store.db_path = str(db_path)
            retriever.vector_store._init_db()
            yield retriever
    
    def test_add_documents(self, rag_retriever):
        """测试添加文档"""
        documents = [
            "Python is a programming language",
            "FastAPI is a web framework",
        ]
        
        doc_ids = rag_retriever.add_knowledge_base(documents)
        assert len(doc_ids) == 2
    
    def test_retrieve_documents(self, rag_retriever):
        """测试检索文档"""
        documents = [
            "Python is a high-level programming language",
            "FastAPI is a modern web framework for Python",
            "Machine learning is a subset of AI",
        ]
        
        rag_retriever.add_knowledge_base(documents)
        
        results = rag_retriever.retrieve(query="Python programming")
        assert len(results) > 0


class TestAgent:
    """Agent测试"""
    
    @pytest.fixture
    def agent(self):
        """创建测试Agent"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 这里可以配置临时数据库路径
            agent = Agent(user_id="test_user")
            yield agent
    
    def test_agent_initialization(self, agent):
        """测试Agent初始化"""
        assert agent.user_id == "test_user"
        assert agent.memory_manager is not None
        assert agent.rag_retriever is not None
    
    def test_add_to_memory(self, agent):
        """测试添加记忆"""
        agent.add_to_memory(
            memory_type=MemoryType.USER_PROFILE,
            content="Test profile",
        )
        
        memories = agent.get_user_memories()
        assert len(memories) > 0
    
    def test_add_knowledge_documents(self, agent):
        """测试添加知识文档"""
        documents = ["Document 1", "Document 2"]
        doc_ids = agent.add_knowledge_documents(documents)
        
        assert len(doc_ids) == 2
    
    def test_clear_conversation(self, agent):
        """测试清除对话"""
        agent.clear_conversation()
        assert len(agent.get_conversation_history()) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
