# 项目架构文档

## 系统架构概览

```
┌─────────────────────────────────────────────────────────┐
│                    User Applications                    │
│              (Web UI / CLI / Other Clients)              │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
        ┌────────────────────────────┐
        │      FastAPI Server        │
        │   (REST API Endpoints)     │
        └────────┬───────────────────┘
                 │
        ┌────────┴──────────────────┬─────────────────┐
        │                           │                 │
        ▼                           ▼                 ▼
    ┌────────┐               ┌──────────┐      ┌──────────┐
    │ Agent  │───────────────│  Memory  │      │   RAG    │
    │ Core   │               │ Manager  │      │Retriever │
    └────────┘               └──────────┘      └──────────┘
        │                         │                  │
        │                         ▼                  ▼
        │                   ┌──────────┐      ┌──────────┐
        │                   │ SQLite   │      │ Vector   │
        │                   │  DB      │      │  Store   │
        │                   │(Memories)│      │ (SQLite) │
        │                   └──────────┘      └──────────┘
        │
        ▼
    ┌────────────────────────────┐
    │    Claude API (Anthropic)  │
    │   (AI Model Backend)       │
    └────────────────────────────┘
```

## 核心模块说明

### 1. Agent 核心模块 (`app/agent/`)

**主要文件**: `agent.py`

**功能**:
- 协调记忆系统、RAG和Claude API
- 管理对话上下文
- 生成动态系统提示
- 记忆提取和更新

**关键类**:
```python
class Agent:
    def __init__(user_id)          # 初始化Agent
    def chat()                      # 对话接口
    def add_to_memory()             # 添加记忆
    def get_user_memories()         # 获取记忆
    def add_knowledge_documents()   # 添加知识库
```

**数据流**:
```
用户输入 → 记忆检索 → RAG检索 → 系统提示构建 → Claude API → 响应生成 → 记忆更新
```

### 2. 记忆管理模块 (`app/memory/`)

**主要文件**: `memory_manager.py`

**特点**:
- 独立于对话历史的持久化存储
- 使用SQLite作为后端数据库
- 支持多种记忆类型
- 自动过期管理

**记忆类型**:
```python
MemoryType:
  - USER_PROFILE          # 用户档案
  - CONVERSATION_SUMMARY  # 对话总结
  - LEARNED_FACTS        # 学习的事实
  - USER_PREFERENCES     # 用户偏好
  - INTERACTION_HISTORY  # 交互历史
  - DOCUMENT_CONTEXT     # 文档上下文
```

**数据库模式**:
```sql
CREATE TABLE memories (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    memory_type TEXT NOT NULL,
    content TEXT NOT NULL,
    metadata TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    expired BOOLEAN
);
```

**关键操作**:
- `create_memory()` - 创建新记忆
- `get_user_memories()` - 获取用户记忆
- `search_memories()` - 搜索记忆
- `update_memory()` - 更新记忆
- `delete_memory()` - 删除记忆

### 3. RAG 系统模块 (`app/rag/`)

**主要文件**: `retriever.py`

**功能**:
- 文档向量化
- 向量存储和索引
- 语义相似度搜索
- 上下文构建

**核心类**:

```python
class Document:
    # 文档对象表示

class VectorStore:
    def add_documents()      # 添加文档
    def search()            # 搜索相似文档
    def get_document()      # 获取单个文档
    def delete_document()   # 删除文档

class RAGRetriever:
    def add_knowledge_base()    # 添加知识库
    def retrieve()              # 检索相关文档
    def build_context()         # 构建RAG上下文
```

**向量化过程**:
```
文本输入 → Embedding Model → 高维向量 → 存储 → 相似度计算 → 排序 → 返回Top-K
```

**数据库模式**:
```sql
CREATE TABLE documents (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    metadata TEXT,
    embedding TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### 4. API 路由模块 (`app/api/`)

**主要文件**: `routes.py`

**端点**:
- `POST /chat` - 对话
- `POST /memory/add` - 添加记忆
- `GET /memory/{user_id}` - 获取记忆
- `POST /knowledge/add` - 添加知识库
- `POST /conversation/clear/{user_id}` - 清除对话
- `GET /conversation/{user_id}` - 获取对话历史
- `GET /stats/{user_id}` - 获取统计

### 5. 配置模块 (`app/config/`)

**主要文件**: `config.py`

**功能**:
- 环境配置管理
- 开发/生产环境切换
- 参数中心化管理

**主要参数**:
- Claude API 配置
- 记忆系统配置
- RAG 配置
- 日志配置
- API 配置

## 数据流示例

### 用户对话流程

```
1. 用户发送消息
   ↓
2. Agent 接收消息
   ├─ 记忆查询: get_user_memories(user_id)
   │  └─ 从SQLite中检索所有用户记忆
   │
   ├─ RAG检索: rag_retriever.retrieve(query)
   │  ├─ 将查询转换为向量
   │  ├─ 计算与所有文档的相似度
   │  └─ 返回Top-K最相关的文档
   │
   └─ 系统提示构建:
      ├─ 基础提示
      ├─ + 用户记忆上下文
      ├─ + RAG检索结果
      └─ + 对话历史（当前会话）
3
4. 调用Claude API
   └─ 获取模型响应

5. 记忆更新
   ├─ 检测关键信息
   ├─ 创建新记忆
   └─ 更新现有记忆

6. 返回响应给用户
```

### 记忆系统流程

```
新信息 → 记忆提取 → 分类 → 存储/更新 → 查询 → 返回

例如:
用户: "我是Python开发者"
  ↓
提取: 用户职业信息
  ↓
分类: USER_PROFILE
  ↓
存储: INSERT INTO memories ...
  ↓
后续查询时检索这个记忆
  ↓
在系统提示中包含此信息
```

### RAG 流程

```
知识库文档 → 分块 → 向量化 → 存储
                          ↓
用户查询 → 向量化 → 相似度搜索 → 排序 → 返回Top-K
                ↓
        构建增强提示 → 送入Claude → 增强的响应
```

## 存储结构

### SQLite 数据库

```
ai_agent/
├── data/
│   ├── memories/
│   │   └── memory.db          # 记忆数据库
│   │       └── memories 表    # 存储用户记忆
│   │
│   └── vectors/
│       └── vectors.db         # 向量数据库
│           └── documents 表   # 存储文档和向量
│
└── logs/
    └── agent.log              # 应用日志
```

## 性能优化

### 1. 数据库优化
- 创建索引加速查询
- 批量插入操作
- 自动清理过期数据

### 2. 向量优化
- 嵌入向量缓存
- 向量相似度的数值优化
- 限制返回结果数量

### 3. API优化
- 异步处理
- 请求验证
- 错误处理

## 扩展点

### 1. 替换Embedding模型
```python
class OpenAIEmbedding(SimpleEmbeddingModel):
    def encode(self, text):
        # 使用OpenAI API
        pass
```

### 2. 集成其他数据库
```python
class PostgresVectorStore(VectorStore):
    # PostgreSQL + pgvector 实现
    pass
```

### 3. 添加新的记忆类型
```python
MemoryType.CUSTOM_TYPE = "custom_type"
```

### 4. 集成其他LLM
```python
class GPT4Agent(Agent):
    # 使用GPT-4替代Claude
    pass
```

## 安全性考虑

1. **API密钥管理**
   - 使用环境变量
   - 不在代码中硬编码

2. **输入验证**
   - Pydantic模型验证
   - 文本长度限制

3. **数据隐私**
   - 用户数据隔离
   - 记忆数据加密（可选）

4. **日志安全**
   - 避免记录敏感信息
   - 日志文件权限管理

## 部署架构

```
├── 本地开发
│   └── 单一进程 (uvicorn)
│
├── Docker容器
│   ├── 单容器部署
│   └── Docker Compose
│
└── 生产环境
    ├── Kubernetes
    ├── 负载均衡
    ├── 分布式内存系统
    └── 持久化存储
```

---

**更新时间**: 2026年5月8日
**版本**: 1.0.0
