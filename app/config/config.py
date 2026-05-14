"""
配置管理模块
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """基础配置"""
    
    # Claude API 配置
    CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "")
    CLAUDE_MODEL = "claude-3-5-sonnet-20241022"
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    EMBEDDING_DIMENSIONS = int(os.getenv("EMBEDDING_DIMENSIONS", "1536"))
    
    # 记忆系统配置
    MEMORY_ENABLED = True
    MEMORY_DB_PATH = os.path.join(
        os.path.dirname(__file__), "../../data/memories/memory.db"
    )
    MAX_MEMORIES = 10
    MEMORY_TTL_DAYS = 30
    MAX_SHORT_TERM_MESSAGES = 8
    SUMMARIZE_EVERY_N_MESSAGES = 6
    
    # RAG 配置
    RAG_ENABLED = True
    QDRANT_PATH = os.getenv(
        "QDRANT_PATH",
        os.path.join(os.path.dirname(__file__), "../../data/qdrant"),
    )
    QDRANT_COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "knowledge_chunks")
    CHUNK_SIZE = 220
    CHUNK_OVERLAP = 40
    TOP_K_RESULTS = 5
    SIMILARITY_THRESHOLD = 0.25
    RAG_CANDIDATE_MULTIPLIER = 3
    DENSE_SCORE_WEIGHT = 0.85
    
    # 日志配置
    LOG_LEVEL = "INFO"
    LOG_FILE = os.path.join(
        os.path.dirname(__file__), "../../logs/agent.log"
    )
    
    # API 配置
    API_HOST = "0.0.0.0"
    API_PORT = 8000
    API_DEBUG = False
    
    # 模型参数
    MAX_TOKENS = 2000
    TEMPERATURE = 0.7
    TOP_P = 0.9
    

class DevelopmentConfig(Config):
    """开发环境配置"""
    API_DEBUG = True
    LOG_LEVEL = "DEBUG"


class ProductionConfig(Config):
    """生产环境配置"""
    API_DEBUG = False
    LOG_LEVEL = "INFO"


def get_config() -> Config:
    """获取配置对象"""
    env = os.getenv("ENVIRONMENT", "development")
    if env == "production":
        return ProductionConfig()
    return DevelopmentConfig()
