# AI Agent with Memory & RAG System

一个先进的AI Agent项目，集成了**Claude的记忆系统**和**RAG（检索增强生成）**功能。这个项目适合作为简历项目展示，展示了现代AI应用开发的最佳实践。

## 🎯 项目特性

### 1. **持久化记忆系统** (Independent Memory System)
- ✅ 使用SQLite持久化存储用户记忆（而不是通过上下文传递）
- ✅ 支持多种记忆类型：用户档案、对话总结、学习事实、用户偏好等
- ✅ 自动记忆过期管理
- ✅ 完整的搜索和检索功能
- ✅ 独立于对话历史的永久存储

### 2. **RAG (检索增强生成)**
- ✅ 向量数据库支持
- ✅ 语义相似度搜索
- ✅ 文档索引和检索
- ✅ 自动上下文注入

### 3. **Claude API集成**
- ✅ 使用最新的Claude模型
- ✅ 自定义系统提示
- ✅ 流式响应支持
- ✅ 完整的错误处理

### 4. **REST API**
- ✅ FastAPI框架
- ✅ 完整的CRUD操作
- ✅ 自动API文档 (Swagger/OpenAPI)
- ✅ 异步支持

### 5. **生产级代码**
- ✅ 完整的日志系统
- ✅ 环境配置管理
- ✅ 单元测试
- ✅ 错误处理和验证

## 📁 项目结构

```
ai_agent/
├── app/
│   ├── agent/              # Agent核心逻辑
│   │   └── agent.py        # 主Agent类
│   ├── memory/             # 记忆系统
│   │   └── memory_manager.py
│   ├── rag/                # RAG系统
│   │   └── retriever.py
│   ├── api/                # API路由
│   │   └── routes.py
│   ├── config/             # 配置管理
│   │   └── config.py
│   └── utils/              # 工具函数
│       └── logging_config.py
├── data/                   # 数据存储
│   ├── memories/          # 记忆数据库
│   └── vectors/           # 向量数据库
├── tests/                  # 测试文件
├── server.py              # 主应用入口
├── test.py                # 集成测试
├── requirements.txt       # 依赖列表
├── .env.example           # 环境配置示例
└── README.md              # 本文件
```

## 🚀 快速开始

### 1. 克隆项目
```bash
git clone <repository-url>
cd ai_agent
```

### 2. 创建虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. 安装依赖
```bash
pip install -r requirements.txt
```

### 4. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 文件，添加你的 CLAUDE_API_KEY
```

### 5. 运行测试
```bash
python test.py
```

### 6. 启动服务器
```bash
python server.py
# 或使用 uvicorn
uvicorn server:app --reload
```

服务器将在 `http://localhost:8000` 启动

访问 API 文档：`http://localhost:8000/docs`

## 📚 API 端点

### 对话
```http
POST /chat
Content-Type: application/json

{
  "user_id": "user_001",
  "message": "你好，告诉我关于Python的信息",
  "use_rag": true,
  "retrieve_k": 3
}
```

### 记忆管理
```http
# 添加记忆
POST /memory/add
{
  "user_id": "user_001",
  "memory_type": "user_preferences",
  "content": "用户喜欢简洁的代码示例",
  "metadata": {"importance": "high"}
}

# 获取记忆
GET /memory/user_001?memory_type=user_preferences
```

### 知识库管理
```http
POST /knowledge/add
{
  "user_id": "user_001",
  "documents": [
    "Python是一种高级编程语言...",
    "FastAPI是一个现代化的Web框架..."
  ],
  "metadata_list": [
    {"topic": "python"},
    {"topic": "fastapi"}
  ]
}
```

### 统计信息
```http
GET /stats/user_001
```

## 🔑 核心概念

### 1. 记忆系统架构

不同于传统的对话历史方式，本项目使用**独立的记忆系统**：

```
用户输入
  ↓
记忆检索 (从SQLite查询)
  ↓
RAG检索 (从向量数据库查询)
  ↓
系统提示 + 记忆上下文 + RAG上下文
  ↓
Claude API
  ↓
响应 + 新记忆更新
```

### 2. 记忆类型

- **USER_PROFILE**: 用户基本信息
- **CONVERSATION_SUMMARY**: 对话总结
- **LEARNED_FACTS**: 学习的事实
- **USER_PREFERENCES**: 用户偏好
- **INTERACTION_HISTORY**: 交互历史
- **DOCUMENT_CONTEXT**: 文档上下文

### 3. RAG工作流

1. **索引**: 将知识库文档转换为向量并存储
2. **检索**: 根据用户查询找到相关文档
3. **增强**: 将检索结果添加到模型提示
4. **生成**: 模型基于增强的提示生成响应

## 💡 使用示例

### Python中使用

```python
from app.agent.agent import Agent
from app.memory.memory_manager import MemoryType

# 创建Agent实例
agent = Agent(user_id="user_001")

# 添加知识库文档
agent.add_knowledge_documents([
    "Python是一种解释型编程语言...",
    "FastAPI是一个现代化的Web框架..."
])

# 添加用户记忆
agent.add_to_memory(
    memory_type=MemoryType.USER_PREFERENCES,
    content="用户喜欢简洁的代码示例"
)

# 与Agent对话
response = agent.chat(
    "告诉我关于Python的信息",
    use_rag=True
)

print(response)

# 获取用户记忆统计
stats = agent.get_memory_stats()
print(stats)
```

### cURL中使用

```bash
# 创建对话
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_001",
    "message": "你好",
    "use_rag": true
  }'

# 获取用户统计
curl -X GET "http://localhost:8000/stats/user_001"
```

## 🛠️ 技术栈

| 层级 | 技术 |
|-----|------|
| **Web框架** | FastAPI, Uvicorn |
| **AI模型** | Claude (Anthropic) |
| **数据存储** | SQLite |
| **向量运算** | NumPy, scikit-learn |
| **类型检查** | Pydantic |
| **测试** | pytest |
| **日志** | Python logging |

## 📊 性能特性

- **异步处理**: 使用FastAPI的async/await
- **向量缓存**: 嵌入向量缓存减少重复计算
- **数据库索引**: 优化查询性能
- **批量操作**: 支持批量添加文档
- **内存管理**: 自动清理过期数据

## 🔒 安全特性

- ✅ API密钥管理（通过环境变量）
- ✅ 输入验证（通过Pydantic）
- ✅ CORS配置
- ✅ 错误处理
- ✅ 日志记录

## 📈 可扩展性

本项目设计易于扩展：

```python
# 自定义记忆类型
class CustomMemoryType:
    MY_TYPE = "my_custom_type"

# 集成不同的embedding模型
class OpenAIEmbedding(SimpleEmbeddingModel):
    def encode(self, text: str):
        # 实现OpenAI API调用
        pass

# 添加数据库支持
# 支持PostgreSQL, MongoDB等
```

## 🧪 测试

```bash
# 运行集成测试
python test.py

# 运行pytest
pytest tests/ -v

# 代码覆盖率
pytest --cov=app tests/
```

## 📝 项目简历描述

### 项目标题
**AI Agent with Advanced Memory System and RAG**

### 项目描述
```
开发了一个企业级AI Agent应用，具有以下核心特性：

1. **独立记忆系统**：实现了持久化的用户记忆存储系统，支持多种记忆类型和自动过期管理，不依赖对话上下文传递。

2. **RAG功能**：集成了检索增强生成技术，通过向量数据库和语义搜索提供上下文感知的生成。

3. **Claude API集成**：完整集成Anthropic的Claude API，实现自适应的系统提示和错误处理。

4. **REST API**：使用FastAPI开发，提供完整的CRUD操作和自动API文档。

5. **生产级代码**：完整的日志系统、环境配置管理、单元测试和错误处理。

技术栈：Python, FastAPI, Claude API, SQLite, NumPy, Pydantic
```

## 🔐 环境变量

```
CLAUDE_API_KEY      # 必需：Claude API密钥
ENVIRONMENT         # 可选：开发/生产环境
API_HOST            # 可选：API主机地址
API_PORT            # 可选：API端口
LOG_LEVEL           # 可选：日志级别
```

## 📦 部署

### Docker部署

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "server.py"]
```

```bash
docker build -t ai-agent .
docker run -p 8000:8000 -e CLAUDE_API_KEY=your_key ai-agent
```

### 云部署

- **AWS**: ECR + ECS / Lambda
- **Google Cloud**: Cloud Run / App Engine
- **Azure**: Container Instances / App Service
- **Heroku**: `git push heroku main`

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License

## 🙋 支持

有问题？请创建Issue或联系维护者。

---

**最后更新**: 2026年5月8日

**项目版本**: 1.0.0

**Python版本**: 3.9+
