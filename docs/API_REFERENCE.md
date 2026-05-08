# API 参考文档

## 基础信息

- **基础URL**: `http://localhost:8000`
- **版本**: 1.0.0
- **格式**: JSON
- **认证**: 无（生产环境建议添加）

## 端点列表

### 1. 健康检查

#### GET /health

检查服务器健康状态。

**响应**:
```json
{
  "status": "healthy",
  "service": "AI Agent with Memory & RAG"
}
```

---

### 2. 对话

#### POST /chat

与Agent进行对话。

**请求体**:
```json
{
  "user_id": "string",           // 必需：用户ID
  "message": "string",           // 必需：用户消息
  "use_rag": true,               // 可选：是否使用RAG，默认true
  "retrieve_k": 3                // 可选：RAG检索文档数，默认3
}
```

**响应**:
```json
{
  "user_id": "user_001",
  "message": "你好",
  "response": "你好！我是AI助手..."
}
```

**示例**:
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_001",
    "message": "什么是Python？",
    "use_rag": true,
    "retrieve_k": 3
  }'
```

**状态码**:
- `200`: 成功
- `500`: 服务器错误

---

### 3. 记忆管理

#### POST /memory/add

添加用户记忆。

**请求体**:
```json
{
  "user_id": "string",                    // 必需：用户ID
  "memory_type": "string",                // 必需：记忆类型
  "content": "string",                    // 必需：记忆内容
  "metadata": {                           // 可选：元数据
    "key": "value"
  }
}
```

**记忆类型**:
- `user_profile`: 用户档案
- `conversation_summary`: 对话总结
- `learned_facts`: 学习的事实
- `user_preferences`: 用户偏好
- `interaction_history`: 交互历史
- `document_context`: 文档上下文

**响应**:
```json
{
  "status": "success",
  "message": "Memory added successfully"
}
```

**示例**:
```bash
curl -X POST "http://localhost:8000/memory/add" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_001",
    "memory_type": "user_preferences",
    "content": "用户喜欢简洁的代码示例",
    "metadata": {"importance": "high"}
  }'
```

---

#### GET /memory/{user_id}

获取用户的记忆。

**查询参数**:
- `memory_type` (可选): 记忆类型，如不指定则返回所有类型

**响应**:
```json
{
  "user_id": "user_001",
  "memories": [
    {
      "id": "uuid",
      "type": "user_preferences",
      "content": "用户喜欢简洁的代码示例",
      "created_at": "2024-01-15T10:30:00",
      "updated_at": "2024-01-15T10:30:00",
      "metadata": {"importance": "high"}
    }
  ],
  "total": 1
}
```

**示例**:
```bash
# 获取所有记忆
curl "http://localhost:8000/memory/user_001"

# 获取特定类型的记忆
curl "http://localhost:8000/memory/user_001?memory_type=user_preferences"
```

---

### 4. 知识库管理

#### POST /knowledge/add

添加知识库文档。

**请求体**:
```json
{
  "user_id": "string",                    // 必需：用户ID
  "documents": [                          // 必需：文档列表
    "文档内容1",
    "文档内容2"
  ],
  "metadata_list": [                      // 可选：元数据列表
    {"topic": "python", "source": "doc"},
    {"topic": "fastapi", "source": "doc"}
  ]
}
```

**响应**:
```json
{
  "status": "success",
  "document_ids": [
    "uuid1",
    "uuid2"
  ],
  "count": 2
}
```

**示例**:
```bash
curl -X POST "http://localhost:8000/knowledge/add" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_001",
    "documents": [
      "Python是一种高级编程语言",
      "FastAPI是现代Web框架"
    ],
    "metadata_list": [
      {"topic": "python"},
      {"topic": "fastapi"}
    ]
  }'
```

---

### 5. 对话管理

#### POST /conversation/clear/{user_id}

清除用户的对话历史。

**路径参数**:
- `user_id`: 用户ID

**响应**:
```json
{
  "status": "success",
  "message": "Conversation cleared successfully"
}
```

**示例**:
```bash
curl -X POST "http://localhost:8000/conversation/clear/user_001"
```

---

#### GET /conversation/{user_id}

获取用户的对话历史。

**路径参数**:
- `user_id`: 用户ID

**响应**:
```json
{
  "user_id": "user_001",
  "history": [
    {
      "role": "user",
      "content": "你好"
    },
    {
      "role": "assistant",
      "content": "你好！有什么可以帮助你的吗？"
    }
  ],
  "total_messages": 2
}
```

**示例**:
```bash
curl "http://localhost:8000/conversation/user_001"
```

---

### 6. 统计信息

#### GET /stats/{user_id}

获取用户的统计信息。

**路径参数**:
- `user_id`: 用户ID

**响应**:
```json
{
  "user_id": "user_001",
  "memory_stats": {
    "total_memories": 5,
    "by_type": {
      "user_profile": 1,
      "user_preferences": 2,
      "learned_facts": 2
    }
  },
  "conversation_length": 10
}
```

**示例**:
```bash
curl "http://localhost:8000/stats/user_001"
```

---

## 数据模型

### ChatRequest
```json
{
  "user_id": "string",
  "message": "string",
  "use_rag": "boolean",
  "retrieve_k": "integer"
}
```

### ChatResponse
```json
{
  "user_id": "string",
  "message": "string",
  "response": "string"
}
```

### MemoryRequest
```json
{
  "user_id": "string",
  "memory_type": "string",
  "content": "string",
  "metadata": "object"
}
```

### MemoryResponse
```json
{
  "memory_id": "string",
  "memory_type": "string",
  "content": "string",
  "created_at": "string (ISO 8601)",
  "updated_at": "string (ISO 8601)"
}
```

### KnowledgeDocumentRequest
```json
{
  "user_id": "string",
  "documents": ["string"],
  "metadata_list": ["object"]
}
```

---

## 错误处理

### 错误响应格式

```json
{
  "detail": "错误描述"
}
```

### 常见错误码

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 500 | 服务器内部错误 |

---

## 速率限制

当前版本没有实现速率限制。生产环境建议添加。

```python
# 使用 slowapi
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/chat")
@limiter.limit("10/minute")
async def chat(request: ChatRequest):
    pass
```

---

## 认证

当前版本使用无认证模式。生产环境建议添加：

```python
from fastapi.security import HTTPBearer, HTTPAuthCredentials

security = HTTPBearer()

@app.post("/chat")
async def chat(
    request: ChatRequest,
    credentials: HTTPAuthCredentials = Depends(security)
):
    # 验证token
    pass
```

---

## 使用示例

### Python 示例

```python
import requests

BASE_URL = "http://localhost:8000"

# 1. 对话
response = requests.post(
    f"{BASE_URL}/chat",
    json={
        "user_id": "user_001",
        "message": "Python是什么？",
        "use_rag": True
    }
)
print(response.json())

# 2. 添加记忆
response = requests.post(
    f"{BASE_URL}/memory/add",
    json={
        "user_id": "user_001",
        "memory_type": "user_preferences",
        "content": "用户喜欢简洁的代码"
    }
)
print(response.json())

# 3. 获取统计
response = requests.get(f"{BASE_URL}/stats/user_001")
print(response.json())
```

### JavaScript 示例

```javascript
const BASE_URL = "http://localhost:8000";

// 对话
fetch(`${BASE_URL}/chat`, {
  method: "POST",
  headers: {
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    user_id: "user_001",
    message: "Python是什么？",
    use_rag: true
  })
})
.then(response => response.json())
.then(data => console.log(data));
```

### cURL 示例

```bash
# 对话
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user_001", "message": "Python是什么？"}'

# 获取记忆
curl http://localhost:8000/memory/user_001

# 获取统计
curl http://localhost:8000/stats/user_001
```

---

## 最佳实践

### 1. 用户ID管理

```python
# 使用一致的用户ID格式
user_id = f"user_{user.id}"
user_id = f"user_{uuid.uuid4()}"
user_id = f"org_{org_id}_user_{user_id}"
```

### 2. 错误处理

```python
try:
    response = requests.post(f"{BASE_URL}/chat", json=payload)
    response.raise_for_status()
    return response.json()
except requests.exceptions.RequestException as e:
    # 处理错误
    pass
```

### 3. 连接池

```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

session = requests.Session()
retry = Retry(connect=3, backoff_factor=0.5)
adapter = HTTPAdapter(max_retries=retry)
session.mount('http://', adapter)
session.mount('https://', adapter)
```

### 4. 异步请求

```python
import aiohttp

async def chat(user_id, message):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{BASE_URL}/chat",
            json={"user_id": user_id, "message": message}
        ) as resp:
            return await resp.json()
```

---

**最后更新**: 2026年5月8日
