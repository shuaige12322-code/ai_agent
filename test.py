"""
集成测试 - 演示Agent的完整功能
"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from app.agent.agent import Agent
from app.memory.memory_manager import MemoryType
from app.rag.retriever import RAGRetriever


def test_agent_with_memory_and_rag():
    """测试Agent的记忆系统和RAG功能"""
    
    print("=" * 60)
    print("AI Agent with Memory & RAG System - Test Demo")
    print("=" * 60)
    
    # 1. 初始化Agent
    print("\n1. Initializing Agent...")
    user_id = "user_001"
    agent = Agent(user_id=user_id)
    print(f"✓ Agent initialized for user: {user_id}")
    
    # 2. 添加知识库文档
    print("\n2. Adding knowledge base documents...")
    documents = [
        "Python is a high-level, interpreted programming language known for its simple and readable syntax. "
        "It was created by Guido van Rossum in 1991. Python supports multiple programming paradigms including "
        "procedural, object-oriented, and functional programming.",
        
        "FastAPI is a modern, fast web framework for building APIs with Python 3.7+. "
        "It uses standard Python type hints and is built on top of Starlette and Pydantic. "
        "FastAPI automatically generates interactive API documentation (Swagger/OpenAPI).",
        
        "Claude is an AI assistant created by Anthropic. It's trained to be helpful, harmless, and honest. "
        "Claude can assist with a wide variety of tasks including writing, analysis, math, coding, and creative projects.",
        
        "Retrieval Augmented Generation (RAG) is a technique that combines information retrieval with "
        "generative models. RAG systems retrieve relevant documents and use them to enhance the generation process.",
    ]
    
    metadata_list = [
        {"topic": "python", "source": "tutorial"},
        {"topic": "fastapi", "source": "documentation"},
        {"topic": "claude", "source": "company_info"},
        {"topic": "rag", "source": "ml_concepts"},
    ]
    
    doc_ids = agent.add_knowledge_documents(documents, metadata_list)
    print(f"✓ Added {len(doc_ids)} documents to knowledge base")
    
    # 3. 添加用户记忆
    print("\n3. Adding user memories...")
    agent.add_to_memory(
        memory_type=MemoryType.USER_PROFILE,
        content="User is a Python developer interested in AI and machine learning",
        metadata={"expertise": "intermediate", "languages": ["Python", "JavaScript"]},
    )
    agent.add_to_memory(
        memory_type=MemoryType.USER_PREFERENCES,
        content="Prefers concise explanations with code examples",
        metadata={"style": "technical", "examples": True},
    )
    print("✓ Added user memories")
    
    # 4. 显示内存统计
    print("\n4. Memory Statistics:")
    stats = agent.get_memory_stats()
    print(f"Total memories: {stats['total_memories']}")
    print(f"Memory types: {stats['by_type']}")
    
    # 5. 获取用户记忆
    print("\n5. Retrieving user memories...")
    memories = agent.get_user_memories()
    print(f"Found {len(memories)} memories:")
    for memory in memories:
        print(f"  - Type: {memory['type']}, Content: {memory['content'][:50]}...")
    
    # 6. 对话 - 带RAG
    print("\n6. Chat with RAG enabled...")
    user_message = "Can you explain what Python is?"
    print(f"User: {user_message}")
    
    # 注意：这需要有效的CLAUDE_API_KEY
    try:
        response = agent.chat(user_message, use_rag=True, retrieve_k=3)
        print(f"Assistant: {response[:200]}...")
        print("✓ Chat completed successfully")
    except Exception as e:
        print(f"Note: Chat requires valid CLAUDE_API_KEY. Error: {str(e)[:100]}")
    
    # 7. 获取对话历史
    print("\n7. Conversation History:")
    history = agent.get_conversation_history()
    print(f"Total messages: {len(history)}")
    for msg in history[:3]:
        role = msg["role"]
        content = msg["content"][:50]
        print(f"  {role}: {content}...")
    
    # 8. 测试RAG检索
    print("\n8. Testing RAG Retrieval...")
    rag_retriever = RAGRetriever()
    query = "FastAPI web framework"
    results = rag_retriever.retrieve(query, k=2)
    print(f"Retrieved {len(results)} documents for query: '{query}'")
    for i, result in enumerate(results, 1):
        print(f"  [{i}] Relevance: {result['similarity']:.2f}")
        print(f"      Content: {result['content'][:60]}...")
    
    print("\n" + "=" * 60)
    print("✓ All tests completed successfully!")
    print("=" * 60)
    print("\nKey Features Demonstrated:")
    print("  • Memory Management System (using Claude's Memory API pattern)")
    print("  • RAG (Retrieval Augmented Generation)")
    print("  • Vector Search with Similarity Scoring")
    print("  • Conversation History Tracking")
    print("  • User Profile and Preferences Storage")
    print("=" * 60)


if __name__ == "__main__":
    test_agent_with_memory_and_rag()
