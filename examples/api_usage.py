"""
API 使用示例
展示如何通过HTTP调用Agent API
"""
import requests
import json

BASE_URL = "http://localhost:8000"


def test_health():
    """测试健康检查"""
    print("1. Testing health check...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Response: {response.json()}\n")


def test_chat():
    """测试对话"""
    print("2. Testing chat...")
    payload = {
        "user_id": "user_001",
        "message": "什么是Python？",
        "use_rag": True,
        "retrieve_k": 3
    }
    
    response = requests.post(
        f"{BASE_URL}/chat",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"User: {data['message']}")
        print(f"Assistant: {data['response'][:200]}...\n")
    else:
        print(f"Error: {response.status_code}")
        print(f"Message: {response.text}\n")


def test_add_knowledge():
    """测试添加知识库"""
    print("3. Testing add knowledge documents...")
    payload = {
        "user_id": "user_001",
        "documents": [
            "Python是一种高级编程语言，以其简洁的语法而闻名。",
            "FastAPI是一个现代化的Web框架，用于构建快速的API。",
            "Claude是由Anthropic创建的AI助手。"
        ],
        "metadata_list": [
            {"topic": "python", "type": "programming"},
            {"topic": "fastapi", "type": "web"},
            {"topic": "claude", "type": "ai"}
        ]
    }
    
    response = requests.post(
        f"{BASE_URL}/knowledge/add",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    data = response.json()
    print(f"Response: {data}\n")


def test_add_memory():
    """测试添加记忆"""
    print("4. Testing add memory...")
    payload = {
        "user_id": "user_001",
        "memory_type": "user_preferences",
        "content": "用户喜欢简洁的代码示例和详细的解释",
        "metadata": {"importance": "high", "category": "preference"}
    }
    
    response = requests.post(
        f"{BASE_URL}/memory/add",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    data = response.json()
    print(f"Response: {data}\n")


def test_get_memories():
    """测试获取记忆"""
    print("5. Testing get memories...")
    response = requests.get(f"{BASE_URL}/memory/user_001")
    
    data = response.json()
    print(f"Total memories: {data['total']}")
    for memory in data['memories']:
        print(f"  - {memory['type']}: {memory['content'][:50]}...\n")


def test_get_stats():
    """测试获取统计"""
    print("6. Testing get stats...")
    response = requests.get(f"{BASE_URL}/stats/user_001")
    
    data = response.json()
    print(f"Memory stats: {data['memory_stats']}")
    print(f"Conversation length: {data['conversation_length']}\n")


def test_get_conversation():
    """测试获取对话历史"""
    print("7. Testing get conversation history...")
    response = requests.get(f"{BASE_URL}/conversation/user_001")
    
    data = response.json()
    print(f"Total messages: {data['total_messages']}")
    for msg in data['history'][:3]:
        print(f"  {msg['role']}: {msg['content'][:50]}...\n")


def test_clear_conversation():
    """测试清除对话"""
    print("8. Testing clear conversation...")
    response = requests.post(f"{BASE_URL}/conversation/clear/user_001")
    
    data = response.json()
    print(f"Response: {data}\n")


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("AI Agent API Test Suite")
    print("=" * 60 + "\n")
    
    try:
        test_health()
        test_add_knowledge()
        test_add_memory()
        test_get_memories()
        test_chat()
        test_get_stats()
        test_get_conversation()
        test_clear_conversation()
        
        print("=" * 60)
        print("✓ All tests completed!")
        print("=" * 60)
        
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the server.")
        print("Please make sure the server is running:")
        print("  python server.py")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    # 如果只想测试特定的功能，取消注释相应的行
    
    # test_health()
    # test_add_knowledge()
    # test_add_memory()
    # test_get_memories()
    # test_chat()
    # test_get_stats()
    # test_get_conversation()
    # test_clear_conversation()
    
    # 运行所有测试
    run_all_tests()
