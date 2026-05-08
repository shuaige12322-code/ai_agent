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
    
    # 记忆系统配置
    MEMORY_ENABLED = True
    MEMORY_STORAGE_PATH = os.path.join(
        os.path.dirname(__file__), "../../data/memories"
    )
    MAX_MEMORIES = 10
    MEMORY_TTL_DAYS = 30
    
    # RAG 配置
    RAG_ENABLED = True
    VECTOR_DB_PATH = os.path.join(
        os.path.dirname(__file__), "../../data/vectors"
    )
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 100
    TOP_K_RESULTS = 5
    SIMILARITY_THRESHOLD = 0.5
    
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
