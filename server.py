"""
FastAPI应用主文件
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config.config import get_config
from app.utils.logging_config import setup_logging
from app.api.routes import router

# 设置日志
logger = setup_logging()

# 创建FastAPI应用
app = FastAPI(
    title="AI Agent with Memory & RAG",
    description="An advanced AI agent with persistent memory system and RAG capabilities",
    version="1.0.0",
)

# 配置
config = get_config()

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含路由
app.include_router(router, tags=["agent"])


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "AI Agent with Memory & RAG",
    }


@app.get("/")
async def root():
    """根路由"""
    return {
        "message": "Welcome to AI Agent API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "chat": "/chat",
            "memory": "/memory/{user_id}",
            "knowledge": "/knowledge/add",
        },
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app,
        host=config.API_HOST,
        port=config.API_PORT,
        log_level=config.LOG_LEVEL.lower(),
    )

