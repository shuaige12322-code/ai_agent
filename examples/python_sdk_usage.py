"""
Python SDK 使用示例
展示如何在Python中直接使用Agent
"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.agent.agent import Agent
from app.memory.memory_manager import MemoryType


def example_1_basic_usage():
    """示例1：基本使用"""
    print("=" * 60)
    print("Example 1: Basic Usage")
    print("=" * 60)
    
    # 创建Agent
    agent = Agent(user_id="demo_user_1")
    
    # 添加知识库
    agent.add_knowledge_documents([
        "Python是一种动态类型的编程语言。",
        "FastAPI是构建API的现代Web框架。"
    ])
    
    print("✓ Agent created and knowledge added\n")


def example_2_memory_system():
    """示例2：记忆系统"""
    print("=" * 60)
    print("Example 2: Memory System")
    print("=" * 60)
    
    agent = Agent(user_id="demo_user_2")
    
    # 添加不同类型的记忆
    agent.add_to_memory(
        memory_type=MemoryType.USER_PROFILE,
        content="用户是一名数据科学家",
        metadata={"experience": "5years"}
    )
    
    agent.add_to_memory(
        memory_type=MemoryType.USER_PREFERENCES,
        content="喜欢简洁的代码示例",
        metadata={"style": "concise"}
    )
    
    # 显示统计
    stats = agent.get_memory_stats()
    print(f"\nMemory Statistics:")
    print(f"Total memories: {stats['total_memories']}")
    print(f"By type: {stats['by_type']}")
    
    # 获取记忆
    memories = agent.get_user_memories(
        memory_type=MemoryType.USER_PROFILE
    )
    print(f"\nUser Profile Memories: {len(memories)}")
    for mem in memories:
        print(f"  - {mem['content']}\n")


def example_3_rag_system():
    """示例3：RAG系统"""
    print("=" * 60)
    print("Example 3: RAG System")
    print("=" * 60)
    
    agent = Agent(user_id="demo_user_3")
    
    # 添加知识库文档
    documents = [
        "NumPy是Python的数值计算库。它提供了高效的多维数组对象。",
        "Pandas是用于数据分析的Python库。它提供DataFrame和Series数据结构。",
        "Scikit-learn是机器学习库。它提供了各种算法用于分类、回归和聚类。"
    ]
    
    metadata = [
        {"library": "numpy", "field": "numerical"},
        {"library": "pandas", "field": "data"},
        {"library": "sklearn", "field": "ml"}
    ]
    
    agent.add_knowledge_documents(documents, metadata)
    print("✓ Added 3 documents to knowledge base\n")
    
    # 模拟RAG检索
    from app.rag.retriever import RAGRetriever
    retriever = RAGRetriever()
    
    query = "Python 数据科学库"
    results = retriever.retrieve(query, k=2)
    
    print(f"Query: '{query}'")
    print(f"Retrieved {len(results)} documents:\n")
    
    for i, result in enumerate(results, 1):
        print(f"[{i}] Relevance: {result['similarity']:.2f}")
        print(f"    Content: {result['content'][:60]}...")
        print(f"    Metadata: {result['metadata']}\n")


def example_4_conversation():
    """示例4：对话管理"""
    print("=" * 60)
    print("Example 4: Conversation Management")
    print("=" * 60)
    
    agent = Agent(user_id="demo_user_4")
    
    # 注意：实际使用需要有效的CLAUDE_API_KEY
    print("Note: This example requires a valid CLAUDE_API_KEY\n")
    
    print("Adding knowledge base...")
    agent.add_knowledge_documents([
        "Python是一种通用编程语言。",
        "它被广泛用于数据科学、Web开发和自动化。"
    ])
    
    print("✓ Knowledge base added\n")
    
    # 模拟对话（不实际调用API）
    try:
        print("Simulated conversation flow:")
        print("1. User sends message")
        print("2. Agent retrieves relevant knowledge")
        print("3. Agent retrieves user memories")
        print("4. Agent generates response using Claude API")
        print("5. Response and memories are stored\n")
        
    except Exception as e:
        print(f"Note: {str(e)[:100]}\n")


def example_5_advanced_features():
    """示例5：高级特性"""
    print("=" * 60)
    print("Example 5: Advanced Features")
    print("=" * 60)
    
    agent = Agent(user_id="demo_user_5")
    
    # 1. 添加多个记忆类型
    print("1. Adding various memory types...")
    
    agent.add_to_memory(
        memory_type=MemoryType.LEARNED_FACTS,
        content="用户学到了Python装饰器的用法",
        metadata={"difficulty": "intermediate"}
    )
    
    agent.add_to_memory(
        memory_type=MemoryType.INTERACTION_HISTORY,
        content="上次讨论了异步编程",
        metadata={"timestamp": "2024-01-15"}
    )
    
    print("✓ Added multiple memory types\n")
    
    # 2. 搜索记忆
    print("2. Searching memories...")
    memories = agent.memory_manager.search_memories(
        user_id="demo_user_5",
        query="Python"
    )
    print(f"Found {len(memories)} memories containing 'Python'\n")
    
    # 3. 内存统计
    print("3. Memory statistics:")
    stats = agent.get_memory_stats()
    for mem_type, count in stats['by_type'].items():
        print(f"  {mem_type}: {count}")
    print()
    
    # 4. 对话历史
    print("4. Conversation history:")
    history = agent.get_conversation_history()
    print(f"Total messages: {len(history)}")
    for msg in history:
        print(f"  {msg['role']}: {msg['content'][:40]}...")
    print()
    
    # 5. 清除对话
    print("5. Clearing conversation...")
    agent.clear_conversation()
    print(f"Remaining messages: {len(agent.get_conversation_history())}\n")


def main():
    """运行所有示例"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + "  AI Agent Python SDK Examples".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    try:
        example_1_basic_usage()
        print()
        
        example_2_memory_system()
        print()
        
        example_3_rag_system()
        print()
        
        example_4_conversation()
        print()
        
        example_5_advanced_features()
        print()
        
        print("=" * 60)
        print("✓ All examples completed successfully!")
        print("=" * 60)
        print()
        
    except ImportError as e:
        print(f"Error: Missing dependency - {e}")
        print("Please install all dependencies: pip install -r requirements.txt")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
