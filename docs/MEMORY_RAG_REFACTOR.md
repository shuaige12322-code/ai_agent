# Memory & RAG Refactor

## Recommendation

For this project, `LangGraph` is the better architectural fit than plain `LangChain`.

Why:

- This project is already a stateful agent, not just a simple chain.
- The runtime needs explicit stages: message analysis, memory recall, knowledge retrieval, response generation, and memory write-back.
- Modern long-term memory patterns in the LangChain ecosystem are built on top of LangGraph stores and persistence.
- LangGraph is the better fit when you want durable execution, thread state, checkpointing, and future human-in-the-loop controls.

What still fits `LangChain`:

- Model adapters
- Tool wrappers
- Document loaders
- Embeddings
- Vector store integrations

In short:

- Use `LangChain` for building blocks.
- Use `LangGraph` for orchestration.

## New local architecture

The codebase was refactored toward a LangGraph-style flow without forcing a hard dependency migration yet.

### Layers

1. Short-term memory
   - Kept in `conversation_history`
   - Only recent turns are injected into prompt context

2. Long-term memory
   - Stored in SQLite via `MemoryManager`
   - Each memory now carries:
     - `memory_type`
     - `summary`
     - `tags`
     - `importance`
     - `confidence`
     - `expires_at`
     - `access_count`
   - Retrieval is relevance-based instead of raw `LIKE` matching

3. Knowledge retrieval
   - Documents are chunked before indexing
   - Retrieval uses hybrid scoring:
     - TF-IDF cosine similarity
     - lexical overlap

4. Agent orchestration
   - `Agent.chat()` now behaves like a state graph:
     - analyze input
     - extract candidate memories
     - retrieve relevant memories
     - retrieve knowledge chunks
     - compose system context
     - generate answer
     - persist interaction and summary

## Files changed

- `app/memory/memory_manager.py`
  - redesigned as a durable memory store with scoring and deduplication

- `app/rag/retriever.py`
  - replaced pseudo-embedding retrieval with chunked hybrid retrieval

- `app/agent/agent.py`
  - moved from monolithic prompt assembly to explicit staged orchestration

- `app/config/config.py`
  - fixed SQLite paths to real database files
  - tuned chunking and retrieval settings

- `tests/test_agent.py`
  - updated tests for new memory and retrieval behavior

## What was wrong before

- Memory storage path pointed at a directory, not a database file.
- Vector storage also pointed at a directory, not a database file.
- Memory retrieval was mostly keyword matching.
- RAG retrieval used a hash-based fake embedding, so semantic quality was weak.
- The agent mixed together memory, retrieval, prompting, and persistence in one linear method.

## Why this design is closer to current best practice

This refactor follows the same broad direction recommended by current LangChain/LangGraph docs:

- separate short-term thread state from long-term cross-thread memory
- store long-term memory as structured records
- make retrieval modular
- prefer explicit orchestration for multi-step agents
- use chunked retrieval for RAG instead of pushing whole documents into prompts

## Next migration step

If you want to go one step further, the clean migration path is:

1. Replace `conversation_history` with LangGraph thread state plus a checkpointer.
2. Replace `MemoryManager` with a LangGraph `Store` implementation.
3. Keep the current retrieval layer, but swap the local TF-IDF approach for real embeddings plus a vector store.
4. Move `Agent.chat()` into a true `StateGraph`.

## Suggested future production stack

- Orchestration: `langgraph`
- Agent components: `langchain`
- Long-term memory: `PostgresStore` or `RedisStore`
- Checkpointing: SQLite locally, Postgres in production
- Knowledge retrieval: pgvector, Qdrant, or Milvus
- Observability: LangSmith
