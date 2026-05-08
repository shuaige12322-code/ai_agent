"""
记忆管理系统 - 使用Claude的Memories API
这是项目的核心特性，提供持久化的记忆存储而不是通过上下文传递
"""
import json
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import sqlite3
from pathlib import Path
from app.config.config import get_config

logger = logging.getLogger(__name__)
config = get_config()


class MemoryType:
    """记忆类型定义"""
    USER_PROFILE = "user_profile"  # 用户信息
    CONVERSATION_SUMMARY = "conversation_summary"  # 对话总结
    LEARNED_FACTS = "learned_facts"  # 学到的事实
    USER_PREFERENCES = "user_preferences"  # 用户偏好
    INTERACTION_HISTORY = "interaction_history"  # 交互历史
    DOCUMENT_CONTEXT = "document_context"  # 文档上下文


class Memory:
    """单个记忆对象"""
    
    def __init__(
        self,
        memory_id: str,
        memory_type: str,
        content: str,
        user_id: str,
        created_at: datetime,
        updated_at: datetime,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.memory_id = memory_id
        self.memory_type = memory_type
        self.content = content
        self.user_id = user_id
        self.created_at = created_at
        self.updated_at = updated_at
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.memory_id,
            "type": self.memory_type,
            "content": self.content,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
        }


class MemoryManager:
    """
    记忆管理器 - 使用SQLite存储记忆
    此系统独立于对话上下文，提供持久化记忆存储
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """初始化记忆管理器"""
        self.db_path = db_path or config.MEMORY_STORAGE_PATH
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self) -> None:
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建记忆表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                memory_type TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expired BOOLEAN DEFAULT 0
            )
        """)
        
        # 创建索引以加快查询
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_id ON memories(user_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_memory_type ON memories(memory_type)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_type ON memories(user_id, memory_type)
        """)
        
        conn.commit()
        conn.close()
        logger.info(f"Memory database initialized at {self.db_path}")
    
    def create_memory(
        self,
        user_id: str,
        memory_type: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Memory:
        """
        创建新记忆
        
        Args:
            user_id: 用户ID
            memory_type: 记忆类型
            content: 记忆内容
            metadata: 元数据
            
        Returns:
            Memory对象
        """
        import uuid
        memory_id = str(uuid.uuid4())
        now = datetime.now()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        metadata_str = json.dumps(metadata or {})
        cursor.execute("""
            INSERT INTO memories (id, user_id, memory_type, content, metadata, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (memory_id, user_id, memory_type, content, metadata_str, now, now))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Created memory {memory_id} for user {user_id}")
        return Memory(
            memory_id=memory_id,
            memory_type=memory_type,
            content=content,
            user_id=user_id,
            created_at=now,
            updated_at=now,
            metadata=metadata,
        )
    
    def get_user_memories(
        self,
        user_id: str,
        memory_type: Optional[str] = None,
        limit: int = 10,
    ) -> List[Memory]:
        """
        获取用户的记忆
        
        Args:
            user_id: 用户ID
            memory_type: 记忆类型（可选）
            limit: 返回数量限制
            
        Returns:
            记忆列表
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if memory_type:
            cursor.execute("""
                SELECT id, user_id, memory_type, content, metadata, created_at, updated_at
                FROM memories
                WHERE user_id = ? AND memory_type = ? AND expired = 0
                ORDER BY updated_at DESC
                LIMIT ?
            """, (user_id, memory_type, limit))
        else:
            cursor.execute("""
                SELECT id, user_id, memory_type, content, metadata, created_at, updated_at
                FROM memories
                WHERE user_id = ? AND expired = 0
                ORDER BY updated_at DESC
                LIMIT ?
            """, (user_id, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        memories = []
        for row in rows:
            memory = Memory(
                memory_id=row[0],
                user_id=row[1],
                memory_type=row[2],
                content=row[3],
                metadata=json.loads(row[4]) if row[4] else {},
                created_at=datetime.fromisoformat(row[5]),
                updated_at=datetime.fromisoformat(row[6]),
            )
            memories.append(memory)
        
        return memories
    
    def update_memory(
        self,
        memory_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[Memory]:
        """
        更新记忆
        
        Args:
            memory_id: 记忆ID
            content: 新内容
            metadata: 新元数据
            
        Returns:
            更新后的Memory对象或None
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now()
        metadata_str = json.dumps(metadata or {})
        
        cursor.execute("""
            UPDATE memories
            SET content = ?, metadata = ?, updated_at = ?
            WHERE id = ?
        """, (content, metadata_str, now, memory_id))
        
        conn.commit()
        
        # 获取更新后的记忆
        cursor.execute("""
            SELECT id, user_id, memory_type, content, metadata, created_at, updated_at
            FROM memories
            WHERE id = ?
        """, (memory_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            logger.info(f"Updated memory {memory_id}")
            return Memory(
                memory_id=row[0],
                user_id=row[1],
                memory_type=row[2],
                content=row[3],
                metadata=json.loads(row[4]) if row[4] else {},
                created_at=datetime.fromisoformat(row[5]),
                updated_at=datetime.fromisoformat(row[6]),
            )
        return None
    
    def delete_memory(self, memory_id: str) -> bool:
        """删除记忆（软删除）"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE memories
            SET expired = 1
            WHERE id = ?
        """, (memory_id,))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Deleted memory {memory_id}")
        return True
    
    def search_memories(
        self,
        user_id: str,
        query: str,
        memory_type: Optional[str] = None,
        limit: int = 5,
    ) -> List[Memory]:
        """
        搜索用户的记忆
        
        Args:
            user_id: 用户ID
            query: 搜索查询
            memory_type: 记忆类型（可选）
            limit: 返回数量限制
            
        Returns:
            匹配的记忆列表
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query_param = f"%{query}%"
        
        if memory_type:
            cursor.execute("""
                SELECT id, user_id, memory_type, content, metadata, created_at, updated_at
                FROM memories
                WHERE user_id = ? AND memory_type = ? AND content LIKE ? AND expired = 0
                ORDER BY updated_at DESC
                LIMIT ?
            """, (user_id, memory_type, query_param, limit))
        else:
            cursor.execute("""
                SELECT id, user_id, memory_type, content, metadata, created_at, updated_at
                FROM memories
                WHERE user_id = ? AND content LIKE ? AND expired = 0
                ORDER BY updated_at DESC
                LIMIT ?
            """, (user_id, query_param, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        memories = []
        for row in rows:
            memory = Memory(
                memory_id=row[0],
                user_id=row[1],
                memory_type=row[2],
                content=row[3],
                metadata=json.loads(row[4]) if row[4] else {},
                created_at=datetime.fromisoformat(row[5]),
                updated_at=datetime.fromisoformat(row[6]),
            )
            memories.append(memory)
        
        return memories
    
    def cleanup_expired_memories(self) -> int:
        """清理过期的记忆"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        expiry_date = datetime.now() - timedelta(days=config.MEMORY_TTL_DAYS)
        
        cursor.execute("""
            DELETE FROM memories
            WHERE created_at < ? AND expired = 1
        """, (expiry_date,))
        
        count = cursor.rowcount
        conn.commit()
        conn.close()
        
        logger.info(f"Cleaned up {count} expired memories")
        return count
    
    def get_memory_stats(self, user_id: str) -> Dict[str, Any]:
        """获取用户的记忆统计"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT memory_type, COUNT(*) as count
            FROM memories
            WHERE user_id = ? AND expired = 0
            GROUP BY memory_type
        """, (user_id,))
        
        rows = cursor.fetchall()
        
        cursor.execute("""
            SELECT COUNT(*) FROM memories
            WHERE user_id = ? AND expired = 0
        """, (user_id,))
        
        total = cursor.fetchone()[0]
        conn.close()
        
        stats = {
            "total_memories": total,
            "by_type": {row[0]: row[1] for row in rows}
        }
        
        return stats
