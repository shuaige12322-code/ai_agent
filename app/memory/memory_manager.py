"""
Memory management primitives for layered agent memory.

This module separates durable user memory from short-term conversation
history and adds lightweight ranking so memory retrieval is closer to how
modern agent stacks treat semantic memory.
"""
import json
import logging
import re
import sqlite3
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from app.config.config import get_config

logger = logging.getLogger(__name__)
config = get_config()


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _tokenize(text: str) -> List[str]:
    return re.findall(r"\w+", text.lower())


class MemoryType:
    """Supported long-term memory buckets."""

    USER_PROFILE = "user_profile"
    USER_PREFERENCES = "user_preferences"
    LONG_TERM_FACT = "long_term_fact"
    CONVERSATION_SUMMARY = "conversation_summary"
    TASK_CONTEXT = "task_context"
    INTERACTION_HISTORY = "interaction_history"


@dataclass
class Memory:
    """A durable memory record."""

    memory_id: str
    memory_type: str
    content: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    summary: str = ""
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    importance: float = 0.5
    confidence: float = 0.5
    access_count: int = 0
    last_accessed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.memory_id,
            "type": self.memory_type,
            "content": self.content,
            "summary": self.summary,
            "tags": self.tags,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
            "importance": self.importance,
            "confidence": self.confidence,
            "access_count": self.access_count,
            "last_accessed_at": (
                self.last_accessed_at.isoformat() if self.last_accessed_at else None
            ),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }


class MemoryManager:
    """
    Long-term memory store with lightweight semantic ranking.

    This keeps the project simple while moving closer to modern agent memory:
    memory records carry importance/confidence metadata, can expire, and are
    retrieved with relevance scoring instead of a plain SQL LIKE query.
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or config.MEMORY_DB_PATH
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                memory_type TEXT NOT NULL,
                content TEXT NOT NULL,
                summary TEXT DEFAULT '',
                tags TEXT DEFAULT '[]',
                metadata TEXT DEFAULT '{}',
                importance REAL DEFAULT 0.5,
                confidence REAL DEFAULT 0.5,
                access_count INTEGER DEFAULT 0,
                last_accessed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                archived INTEGER DEFAULT 0
            )
            """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_memories_user_id ON memories(user_id)"
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_memories_user_type
            ON memories(user_id, memory_type)
            """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_memories_active
            ON memories(user_id, archived, updated_at)
            """
        )
        conn.commit()
        conn.close()
        logger.info("Memory database initialized at %s", self.db_path)

    def create_memory(
        self,
        user_id: str,
        memory_type: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        importance: float = 0.6,
        confidence: float = 0.7,
        tags: Optional[Sequence[str]] = None,
        expires_at: Optional[datetime] = None,
    ) -> Memory:
        memory_id = str(uuid.uuid4())
        now = _utcnow()
        summary = self._build_summary(content)
        memory = Memory(
            memory_id=memory_id,
            memory_type=memory_type,
            content=content.strip(),
            summary=summary,
            tags=list(tags or []),
            user_id=user_id,
            created_at=now,
            updated_at=now,
            metadata=metadata or {},
            importance=max(0.0, min(1.0, importance)),
            confidence=max(0.0, min(1.0, confidence)),
            expires_at=expires_at,
        )

        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO memories (
                id, user_id, memory_type, content, summary, tags, metadata,
                importance, confidence, access_count, last_accessed_at,
                created_at, updated_at, expires_at, archived
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
            """,
            (
                memory.memory_id,
                memory.user_id,
                memory.memory_type,
                memory.content,
                memory.summary,
                json.dumps(memory.tags),
                json.dumps(memory.metadata),
                memory.importance,
                memory.confidence,
                memory.access_count,
                None,
                memory.created_at.isoformat(),
                memory.updated_at.isoformat(),
                memory.expires_at.isoformat() if memory.expires_at else None,
            ),
        )
        conn.commit()
        conn.close()
        return memory

    def create_or_update_memory(
        self,
        user_id: str,
        memory_type: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        importance: float = 0.6,
        confidence: float = 0.7,
        tags: Optional[Sequence[str]] = None,
        dedupe_threshold: float = 0.82,
    ) -> Memory:
        candidates = self.get_user_memories(
            user_id=user_id,
            memory_type=memory_type,
            limit=25,
        )
        content_tokens = set(_tokenize(content))

        for memory in candidates:
            score = self._token_overlap_score(
                content_tokens,
                set(_tokenize(memory.content)),
            )
            if score >= dedupe_threshold:
                merged_metadata = dict(memory.metadata)
                merged_metadata.update(metadata or {})
                merged_tags = sorted(set(memory.tags) | set(tags or []))
                return self.update_memory(
                    memory_id=memory.memory_id,
                    content=content,
                    metadata=merged_metadata,
                    importance=max(memory.importance, importance),
                    confidence=max(memory.confidence, confidence),
                    tags=merged_tags,
                )

        return self.create_memory(
            user_id=user_id,
            memory_type=memory_type,
            content=content,
            metadata=metadata,
            importance=importance,
            confidence=confidence,
            tags=tags,
        )

    def _row_to_memory(self, row: sqlite3.Row) -> Memory:
        return Memory(
            memory_id=row["id"],
            user_id=row["user_id"],
            memory_type=row["memory_type"],
            content=row["content"],
            summary=row["summary"] or "",
            tags=json.loads(row["tags"] or "[]"),
            metadata=json.loads(row["metadata"] or "{}"),
            importance=float(row["importance"] or 0.0),
            confidence=float(row["confidence"] or 0.0),
            access_count=int(row["access_count"] or 0),
            last_accessed_at=(
                datetime.fromisoformat(row["last_accessed_at"])
                if row["last_accessed_at"]
                else None
            ),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            expires_at=(
                datetime.fromisoformat(row["expires_at"]) if row["expires_at"] else None
            ),
        )

    def get_user_memories(
        self,
        user_id: str,
        memory_type: Optional[str] = None,
        limit: int = 10,
    ) -> List[Memory]:
        conn = self._connect()
        cursor = conn.cursor()
        now_iso = _utcnow().isoformat()
        if memory_type:
            cursor.execute(
                """
                SELECT * FROM memories
                WHERE user_id = ?
                  AND memory_type = ?
                  AND archived = 0
                  AND (expires_at IS NULL OR expires_at > ?)
                ORDER BY updated_at DESC
                LIMIT ?
                """,
                (user_id, memory_type, now_iso, limit),
            )
        else:
            cursor.execute(
                """
                SELECT * FROM memories
                WHERE user_id = ?
                  AND archived = 0
                  AND (expires_at IS NULL OR expires_at > ?)
                ORDER BY updated_at DESC
                LIMIT ?
                """,
                (user_id, now_iso, limit),
            )
        rows = cursor.fetchall()
        conn.close()
        return [self._row_to_memory(row) for row in rows]

    def update_memory(
        self,
        memory_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        importance: Optional[float] = None,
        confidence: Optional[float] = None,
        tags: Optional[Sequence[str]] = None,
    ) -> Memory:
        existing = self.get_memory(memory_id)
        if existing is None:
            raise ValueError(f"Memory {memory_id} not found")

        now = _utcnow()
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE memories
            SET content = ?,
                summary = ?,
                metadata = ?,
                importance = ?,
                confidence = ?,
                tags = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                content.strip(),
                self._build_summary(content),
                json.dumps(metadata or existing.metadata),
                importance if importance is not None else existing.importance,
                confidence if confidence is not None else existing.confidence,
                json.dumps(list(tags or existing.tags)),
                now.isoformat(),
                memory_id,
            ),
        )
        conn.commit()
        conn.close()
        updated = self.get_memory(memory_id)
        if updated is None:
            raise ValueError(f"Memory {memory_id} disappeared after update")
        return updated

    def get_memory(self, memory_id: str) -> Optional[Memory]:
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM memories WHERE id = ?", (memory_id,))
        row = cursor.fetchone()
        conn.close()
        return self._row_to_memory(row) if row else None

    def delete_memory(self, memory_id: str) -> bool:
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("UPDATE memories SET archived = 1 WHERE id = ?", (memory_id,))
        conn.commit()
        deleted = cursor.rowcount > 0
        conn.close()
        return deleted

    def search_memories(
        self,
        user_id: str,
        query: str,
        memory_type: Optional[str] = None,
        limit: int = 5,
    ) -> List[Memory]:
        return self.get_relevant_memories(
            user_id=user_id,
            query=query,
            memory_types=[memory_type] if memory_type else None,
            limit=limit,
        )

    def get_relevant_memories(
        self,
        user_id: str,
        query: str,
        memory_types: Optional[Sequence[str]] = None,
        limit: int = 5,
    ) -> List[Memory]:
        memories = self.get_user_memories(user_id=user_id, limit=max(limit * 8, 30))
        if memory_types:
            allowed = set(memory_types)
            memories = [memory for memory in memories if memory.memory_type in allowed]

        query_tokens = set(_tokenize(query))
        ranked: List[tuple[float, Memory]] = []
        for memory in memories:
            score = self._memory_score(memory, query_tokens)
            if score > 0.12:
                ranked.append((score, memory))

        ranked.sort(key=lambda item: item[0], reverse=True)
        selected = [memory for _, memory in ranked[:limit]]
        for memory in selected:
            self.record_memory_access(memory.memory_id)
        return selected

    def record_memory_access(self, memory_id: str) -> None:
        conn = self._connect()
        cursor = conn.cursor()
        now = _utcnow().isoformat()
        cursor.execute(
            """
            UPDATE memories
            SET access_count = access_count + 1,
                last_accessed_at = ?
            WHERE id = ?
            """,
            (now, memory_id),
        )
        conn.commit()
        conn.close()

    def build_memory_context(self, user_id: str, query: str, limit: int = 5) -> str:
        relevant = self.get_relevant_memories(
            user_id=user_id,
            query=query,
            limit=limit,
        )
        if not relevant:
            return "No durable user memory matched the current request."

        lines = ["Relevant user memory:"]
        for memory in relevant:
            tags = f" tags={','.join(memory.tags)}" if memory.tags else ""
            lines.append(
                f"- [{memory.memory_type}] {memory.content} "
                f"(importance={memory.importance:.2f}, confidence={memory.confidence:.2f}{tags})"
            )
        return "\n".join(lines)

    def cleanup_expired_memories(self) -> int:
        cutoff = _utcnow() - timedelta(days=config.MEMORY_TTL_DAYS)
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            DELETE FROM memories
            WHERE archived = 1
               OR (expires_at IS NOT NULL AND expires_at <= ?)
               OR (memory_type = ? AND updated_at <= ?)
            """,
            (
                _utcnow().isoformat(),
                MemoryType.INTERACTION_HISTORY,
                cutoff.isoformat(),
            ),
        )
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        return deleted

    def get_memory_stats(self, user_id: str) -> Dict[str, Any]:
        memories = self.get_user_memories(user_id=user_id, limit=500)
        by_type: Dict[str, int] = {}
        for memory in memories:
            by_type[memory.memory_type] = by_type.get(memory.memory_type, 0) + 1

        return {
            "total_memories": len(memories),
            "by_type": by_type,
            "avg_importance": (
                sum(memory.importance for memory in memories) / len(memories)
                if memories
                else 0.0
            ),
        }

    def _memory_score(self, memory: Memory, query_tokens: set[str]) -> float:
        content_tokens = set(
            _tokenize(memory.content + " " + memory.summary + " " + " ".join(memory.tags))
        )
        lexical = self._token_overlap_score(query_tokens, content_tokens)
        age_days = max((_utcnow() - memory.updated_at).days, 0)
        recency = max(0.0, 1.0 - min(age_days / max(config.MEMORY_TTL_DAYS, 1), 1.0))

        return (
            lexical * 0.55
            + memory.importance * 0.2
            + memory.confidence * 0.15
            + recency * 0.1
        )

    @staticmethod
    def _token_overlap_score(left: set[str], right: set[str]) -> float:
        if not left or not right:
            return 0.0
        intersection = len(left & right)
        union = len(left | right)
        return intersection / union if union else 0.0

    @staticmethod
    def _build_summary(content: str, max_length: int = 120) -> str:
        normalized = " ".join(content.strip().split())
        if len(normalized) <= max_length:
            return normalized
        return normalized[: max_length - 3] + "..."
