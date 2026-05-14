"""
FastAPI路由 - Agent API端点
"""
import json
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.agent.agent import Agent
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# 存储活跃的Agent实例
agents: Dict[str, Agent] = {}


class ChatRequest(BaseModel):
    """对话请求"""
    user_id: str
    message: str
    use_rag: bool = True
    retrieve_k: int = 3


class ChatResponse(BaseModel):
    """对话响应"""
    user_id: str
    message: str
    response: str


def _sse_event(event: str, data: Dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


class MemoryRequest(BaseModel):
    """记忆请求"""
    user_id: str
    memory_type: str
    content: str
    metadata: Optional[Dict[str, Any]] = None


class KnowledgeDocumentRequest(BaseModel):
    """知识文档请求"""
    user_id: str
    documents: List[str]
    metadata_list: Optional[List[Dict[str, Any]]] = None


class MemoryResponse(BaseModel):
    """记忆响应"""
    memory_id: str
    memory_type: str
    content: str
    created_at: str
    updated_at: str


def get_agent(user_id: str) -> Agent:
    """获取或创建Agent实例"""
    if user_id not in agents:
        agents[user_id] = Agent(user_id=user_id)
        logger.info(f"Created new agent for user {user_id}")
    return agents[user_id]


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    与Agent进行对话
    
    Args:
        request: 对话请求
        
    Returns:
        对话响应
    """
    try:
        agent = get_agent(request.user_id)
        
        response = agent.chat(
            user_message=request.message,
            use_rag=request.use_rag,
            retrieve_k=request.retrieve_k,
        )
        
        return ChatResponse(
            user_id=request.user_id,
            message=request.message,
            response=response,
        )
        
    except Exception as e:
        logger.error(f"Error in chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/stream")
async def stream_chat(request: ChatRequest) -> StreamingResponse:
    """Stream assistant responses as server-sent events."""

    def event_stream():
        try:
            agent = get_agent(request.user_id)
            for chunk in agent.stream_chat(
                user_message=request.message,
                use_rag=request.use_rag,
                retrieve_k=request.retrieve_k,
            ):
                yield _sse_event("token", {"delta": chunk})
            yield _sse_event("done", {"status": "complete"})
        except Exception as e:
            logger.error(f"Error in stream_chat: {e}")
            yield _sse_event("error", {"detail": str(e)})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/memory/add")
async def add_memory(request: MemoryRequest) -> Dict[str, Any]:
    """
    添加用户记忆
    
    Args:
        request: 记忆请求
        
    Returns:
        创建的记忆
    """
    try:
        agent = get_agent(request.user_id)
        agent.add_to_memory(
            memory_type=request.memory_type,
            content=request.content,
            metadata=request.metadata,
        )
        
        return {
            "status": "success",
            "message": "Memory added successfully",
        }
        
    except Exception as e:
        logger.error(f"Error adding memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memory/{user_id}")
async def get_memories(
    user_id: str,
    memory_type: Optional[str] = None,
) -> Dict[str, Any]:
    """
    获取用户的记忆
    
    Args:
        user_id: 用户ID
        memory_type: 记忆类型（可选）
        
    Returns:
        记忆列表
    """
    try:
        agent = get_agent(user_id)
        memories = agent.get_user_memories(memory_type=memory_type)
        
        return {
            "user_id": user_id,
            "memories": memories,
            "total": len(memories),
        }
        
    except Exception as e:
        logger.error(f"Error getting memories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/knowledge/add")
async def add_knowledge_documents(
    request: KnowledgeDocumentRequest,
) -> Dict[str, Any]:
    """
    添加知识库文档
    
    Args:
        request: 知识文档请求
        
    Returns:
        添加结果
    """
    try:
        agent = get_agent(request.user_id)
        doc_ids = agent.add_knowledge_documents(
            documents=request.documents,
            metadata_list=request.metadata_list,
        )
        
        return {
            "status": "success",
            "document_ids": doc_ids,
            "count": len(doc_ids),
        }
        
    except Exception as e:
        logger.error(f"Error adding knowledge documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/conversation/clear/{user_id}")
async def clear_conversation(user_id: str) -> Dict[str, str]:
    """
    清除对话历史
    
    Args:
        user_id: 用户ID
        
    Returns:
        清除结果
    """
    try:
        agent = get_agent(user_id)
        agent.clear_conversation()
        
        return {
            "status": "success",
            "message": "Conversation cleared successfully",
        }
        
    except Exception as e:
        logger.error(f"Error clearing conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversation/{user_id}")
async def get_conversation_history(user_id: str) -> Dict[str, Any]:
    """
    获取对话历史
    
    Args:
        user_id: 用户ID
        
    Returns:
        对话历史
    """
    try:
        agent = get_agent(user_id)
        history = agent.get_conversation_history()
        
        return {
            "user_id": user_id,
            "history": history,
            "total_messages": len(history),
        }
        
    except Exception as e:
        logger.error(f"Error getting conversation history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/{user_id}")
async def get_user_stats(user_id: str) -> Dict[str, Any]:
    """
    获取用户统计
    
    Args:
        user_id: 用户ID
        
    Returns:
        用户统计
    """
    try:
        agent = get_agent(user_id)
        memory_stats = agent.get_memory_stats()
        history = agent.get_conversation_history()
        
        return {
            "user_id": user_id,
            "memory_stats": memory_stats,
            "conversation_length": len(history),
        }
        
    except Exception as e:
        logger.error(f"Error getting user stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
