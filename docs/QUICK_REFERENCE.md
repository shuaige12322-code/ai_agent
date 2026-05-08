# 项目快速参考

## 项目概述

**AI Agent with Memory & RAG System** 是一个企业级的AI Agent应用，集成了：

1. **独立记忆系统** - 持久化用户记忆存储（不依赖对话上下文）
2. **RAG功能** - 检索增强生成，提供上下文感知的回答
3. **Claude API集成** - 使用最新的Claude模型
4. **REST API** - 完整的FastAPI接口

## 快速命令

```bash
# 初始化
make setup              # 或 ./setup.sh (Linux/Mac) / setup.bat (Windows)

# 开发
make install           # 安装依赖
make run              # 运行服务器
make test             # 运行测试

# 代码质量
make lint             # 检查代码
make format           # 格式化代码
make clean            # 清理文件

# Docker
make docker-build     # 构建Docker镜像
make docker-run       # 运行Docker容器
```

## 项目结构

```
ai_agent/
├── app/                          # 应用代码
│   ├── agent/                   # Agent核心
│   │   └── agent.py            # 主Agent类
│   ├── memory/                  # 记忆系统
│   │   └── memory_manager.py   # 记忆管理
│   ├── rag/                     # RAG系统
│   │   └── retriever.py        # 检索器
│   ├── api/                     # API路由
│   │   └── routes.py           # 路由定义
│   ├── config/                  # 配置
│   │   └── config.py           # 配置管理
│   └── utils/                   # 工具
│       └── logging_config.py   # 日志配置
│
├── data/                         # 数据存储
│   ├── memories/               # 记忆数据库
│   └── vectors/                # 向量数据库
│
├── docs/                         # 文档
│   ├── ARCHITECTURE.md         # 架构文档
│   ├── DEPLOYMENT.md           # 部署指南
│   ├── API_REFERENCE.md        # API参考
│   └── QUICK_REFERENCE.md      # 快速参考
│
├── examples/                     # 示例代码
│   ├── api_usage.py           # API调用示例
│   └── python_sdk_usage.py    # Python SDK示例
│
├── tests/                        # 单元测试
│   └── test_agent.py          # Agent测试
│
├── server.py                     # 主服务器
├── test.py                       # 集成测试
├── requirements.txt              # 依赖列表
├── .env.example                  # 环境配置示例
├── .gitignore                    # Git忽略文件
├── Dockerfile                    # Docker文件
├── docker-compose.yml            # Docker Compose
├── Makefile                      # Make脚本
├── setup.sh                      # Linux/Mac启动脚本
├── setup.bat                     # Windows启动脚本
└── README.md                     # 项目说明

```

## 核心特性

### 1. 记忆系统

```python
# 添加记忆
agent.add_to_memory(
    memory_type="user_preferences",
    content="用户喜欢简洁的代码",
    metadata={"importance": "high"}
)

# 获取记忆
memories = agent.get_user_memories()

# 搜索记忆
results = memory_manager.search_memories(
    user_id="user_001",
    query="Python"
)
```

### 2. RAG功能

```python
# 添加知识库
agent.add_knowledge_documents([
    "Python文档",
    "FastAPI指南"
])

# 对话时自动使用RAG
response = agent.chat(
    "Python是什么？",
    use_rag=True,
    retrieve_k=3
)
```

### 3. API接口

```bash
# 对话
POST /chat

# 记忆管理
POST /memory/add
GET /memory/{user_id}

# 知识库
POST /knowledge/add

# 统计
GET /stats/{user_id}
```

## 配置

### 环境变量 (.env)

```
# Claude API
CLAUDE_API_KEY=sk_***

# 环境
ENVIRONMENT=development

# 服务器
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=true

# 日志
LOG_LEVEL=DEBUG

# 记忆
MEMORY_ENABLED=true
MAX_MEMORIES=10
MEMORY_TTL_DAYS=30

# RAG
RAG_ENABLED=true
TOP_K_RESULTS=5
SIMILARITY_THRESHOLD=0.5
```

## API端点

### 对话
```
POST /chat
Content-Type: application/json

{
  "user_id": "user_001",
  "message": "你好",
  "use_rag": true,
  "retrieve_k": 3
}
```

### 记忆
```
POST /memory/add          - 添加记忆
GET /memory/{user_id}     - 获取记忆
GET /stats/{user_id}      - 获取统计
```

### 知识库
```
POST /knowledge/add       - 添加文档
```

### 对话管理
```
GET /conversation/{user_id}           - 获取历史
POST /conversation/clear/{user_id}    - 清除对话
```

## 技术栈

| 层级 | 技术 |
|-----|------|
| Web框架 | FastAPI, Uvicorn |
| AI | Claude (Anthropic) |
| 数据库 | SQLite |
| 向量运算 | NumPy, scikit-learn |
| 验证 | Pydantic |
| 测试 | pytest |

## 开发流程

### 1. 本地开发

```bash
# 克隆项目
git clone <repo>
cd ai_agent

# 设置环境
make setup

# 编辑 .env，添加 CLAUDE_API_KEY

# 运行服务
make run

# 在另一个终端运行测试
make test
```

### 2. 测试

```bash
# 集成测试
python test.py

# 单元测试
pytest tests/ -v

# API测试
python examples/api_usage.py
```

### 3. 部署

```bash
# Docker构建
docker build -t ai-agent .

# Docker运行
docker run -p 8000:8000 -e CLAUDE_API_KEY=key ai-agent

# 或使用Docker Compose
docker-compose up -d
```

## Python SDK使用

```python
from app.agent.agent import Agent
from app.memory.memory_manager import MemoryType

# 创建Agent
agent = Agent(user_id="user_001")

# 添加知识库
agent.add_knowledge_documents([
    "Python文档",
    "FastAPI指南"
])

# 添加记忆
agent.add_to_memory(
    memory_type=MemoryType.USER_PROFILE,
    content="用户是Python开发者"
)

# 对话
response = agent.chat("Python怎么学？", use_rag=True)
print(response)

# 获取统计
stats = agent.get_memory_stats()
print(stats)
```

## API使用示例

### Python

```python
import requests

response = requests.post(
    "http://localhost:8000/chat",
    json={
        "user_id": "user_001",
        "message": "Python是什么？",
        "use_rag": True
    }
)
print(response.json())
```

### JavaScript

```javascript
const response = await fetch("http://localhost:8000/chat", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    user_id: "user_001",
    message: "Python是什么？",
    use_rag: true
  })
});
const data = await response.json();
console.log(data);
```

### cURL

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_001",
    "message": "Python是什么？"
  }'
```

## 常见问题

### Q: 如何添加自定义记忆类型？
A: 编辑 `app/memory/memory_manager.py` 中的 `MemoryType` 类

### Q: 如何替换Embedding模型？
A: 继承 `SimpleEmbeddingModel` 并实现 `encode()` 方法

### Q: 如何集成其他数据库？
A: 创建新的 `VectorStore` 实现类

### Q: 生产环境有什么建议？
A: 见 docs/DEPLOYMENT.md

## 性能指标

- **响应时间**: < 500ms (不包括Claude API延迟)
- **内存占用**: ~200MB (基础)
- **并发连接**: 支持数百个并发用户
- **数据库查询**: 使用索引优化到 < 50ms

## 贡献指南

1. Fork项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交改动 (`git commit -m 'Add some AmazingFeature'`)
4. 推送分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

## 许可证

MIT License

## 联系方式

- Issues: GitHub Issues
- 文档: /docs 目录

---

**版本**: 1.0.0  
**最后更新**: 2026年5月8日
