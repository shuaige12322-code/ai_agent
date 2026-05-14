# AI Agent with Layered Memory and RAG

一个基于 `FastAPI + Claude + OpenAI Embeddings + Qdrant` 的 AI Agent 项目。

这个项目的目标不是只做一个聊天接口，而是提供一套更接近真实 Agent 的后端骨架：

- 有短期会话记忆
- 有长期用户记忆
- 有知识库检索增强生成
- 有可持续演进到 `LangGraph` 的状态流结构

## 核心能力

### 1. 分层记忆

项目把记忆分成两层：

- 短期记忆
  - 保存在当前 `conversation_history`
  - 只把最近几轮对话送进 prompt

- 长期记忆
  - 由 `MemoryManager` 管理
  - 存储在 SQLite
  - 支持：
    - `memory_type`
    - `summary`
    - `tags`
    - `importance`
    - `confidence`
    - `expires_at`
    - `access_count`

### 2. RAG 检索

当前 RAG 已经升级为真实向量检索：

- 文档先切块
- 使用 `OpenAI Embeddings` 生成向量
- 使用本地 `Qdrant` 保存和检索向量
- 查询时使用 dense retrieval
- 再叠加轻量 lexical overlap 做重排

默认 embedding 模型：

- `text-embedding-3-small`

### 3. Agent 编排

`Agent.chat()` 当前流程：

1. 分析用户输入
2. 提取候选记忆
3. 召回长期记忆
4. 检索知识库 chunk
5. 组装上下文
6. 调用 Claude 生成回复
7. 回写交互记忆和摘要

这套结构已经很接近 `LangGraph` 的思路：

- `LangChain` 更适合做组件层
- `LangGraph` 更适合做后续的工作流编排层

## 技术栈

- Python 3.10+
- FastAPI
- Anthropic Claude
- OpenAI Embeddings
- Qdrant local mode
- SQLite
- Pytest

## 项目结构

```text
ai_agent/
├── app/
│   ├── agent/
│   │   └── agent.py
│   ├── api/
│   │   └── routes.py
│   ├── config/
│   │   └── config.py
│   ├── memory/
│   │   └── memory_manager.py
│   ├── rag/
│   │   └── retriever.py
│   └── utils/
├── data/
│   ├── memories/
│   │   └── memory.db
│   └── qdrant/
├── docs/
│   └── MEMORY_RAG_REFACTOR.md
├── tests/
│   └── test_agent.py
├── server.py
├── requirements.txt
└── .env.example
```

## 关键文件

- [app/agent/agent.py](c:/Users/Admin/Desktop/ai_agent/app/agent/agent.py)
  - Agent 主流程

- [app/memory/memory_manager.py](c:/Users/Admin/Desktop/ai_agent/app/memory/memory_manager.py)
  - 长期记忆存储、召回、去重、统计

- [app/rag/retriever.py](c:/Users/Admin/Desktop/ai_agent/app/rag/retriever.py)
  - 文档切块、embedding、Qdrant 检索、上下文构建

- [app/config/config.py](c:/Users/Admin/Desktop/ai_agent/app/config/config.py)
  - 所有运行参数与路径配置

## 安装

### 1. 创建虚拟环境

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 2. 安装依赖

```bash
python -m pip install -r requirements.txt
```

### 3. 配置环境变量

复制环境变量示例文件：

```bash
copy .env.example .env
```

至少需要配置：

```env
CLAUDE_API_KEY=your_claude_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
ENVIRONMENT=development
```

可选配置：

```env
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSIONS=1536
QDRANT_PATH=./data/qdrant
QDRANT_COLLECTION_NAME=knowledge_chunks
```

## 运行项目

```bash
python server.py
```

启动后访问：

```text
http://localhost:8000/docs
```

## 测试

运行测试：

```bash
python -m pytest tests\test_agent.py -q
```

当前已验证通过：

```text
11 passed
```

## API 概览

### 聊天

`POST /chat`

示例请求：

```json
{
  "user_id": "user_001",
  "message": "Tell me about Python web frameworks",
  "use_rag": true,
  "retrieve_k": 3
}
```

### 添加记忆

`POST /memory/add`

### 获取记忆

`GET /memory/{user_id}`

### 添加知识库文档

`POST /knowledge/add`

### 获取统计

`GET /stats/{user_id}`

## 当前配置说明

### 记忆

- `MEMORY_DB_PATH`
  - 长期记忆 SQLite 路径

- `MAX_MEMORIES`
  - 每轮召回的最大记忆数

- `MEMORY_TTL_DAYS`
  - 记忆保留周期

### RAG

- `QDRANT_PATH`
  - 本地 Qdrant 数据目录

- `QDRANT_COLLECTION_NAME`
  - 向量集合名称

- `CHUNK_SIZE`
  - 文本切块大小

- `CHUNK_OVERLAP`
  - 切块重叠长度

- `SIMILARITY_THRESHOLD`
  - 检索结果最低分数阈值

- `DENSE_SCORE_WEIGHT`
  - dense score 在重排中的权重


