"""
RAG (检索增强生成) 系统
提供向量数据库和语义搜索功能
"""
import json
import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import sqlite3
from datetime import datetime
from app.config.config import get_config

logger = logging.getLogger(__name__)
config = get_config()


class Document:
    """文档对象"""
    
    def __init__(
        self,
        doc_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        embedding: Optional[List[float]] = None,
    ):
        self.doc_id = doc_id
        self.content = content
        self.metadata = metadata or {}
        self.embedding = embedding
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.doc_id,
            "content": self.content,
            "metadata": self.metadata,
            "embedding": self.embedding,
        }


class SimpleEmbeddingModel:
    """
    简单的向量化模型
    在实际项目中可以替换为OpenAI Embeddings或其他模型
    """
    
    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self._cache = {}
    
    def encode(self, text: str) -> List[float]:
        """
        生成文本的嵌入向量
        这是一个简化的实现，实际项目应使用真实的embedding模型
        """
        if text in self._cache:
            return self._cache[text]
        
        # 使用简单的哈希和数值转换生成向量
        import hashlib
        hash_obj = hashlib.md5(text.encode())
        hash_bytes = hash_obj.digest()
        
        # 将哈希转换为浮点向量
        embedding = []
        for i in range(self.dimension):
            byte_index = i % len(hash_bytes)
            value = (hash_bytes[byte_index] - 128) / 128.0
            embedding.append(value)
        
        self._cache[text] = embedding
        return embedding
    
    def similarity(
        self,
        embedding1: List[float],
        embedding2: List[float],
    ) -> float:
        """计算两个向量的余弦相似度"""
        arr1 = np.array(embedding1)
        arr2 = np.array(embedding2)
        
        # 计算余弦相似度
        dot_product = np.dot(arr1, arr2)
        norm1 = np.linalg.norm(arr1)
        norm2 = np.linalg.norm(arr2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)


class VectorStore:
    """向量存储 - 用于存储文档和其嵌入向量"""
    
    def __init__(self, db_path: Optional[str] = None):
        """初始化向量存储"""
        self.db_path = db_path or config.VECTOR_DB_PATH
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.embedding_model = SimpleEmbeddingModel()
        self._init_db()
    
    def _init_db(self) -> None:
        """初始化向量数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                metadata TEXT,
                embedding TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_created_at ON documents(created_at)
        """)
        
        conn.commit()
        conn.close()
        logger.info(f"Vector store initialized at {self.db_path}")
    
    def add_documents(self, documents: List[Document]) -> List[str]:
        """
        添加文档到向量存储
        
        Args:
            documents: 文档列表
            
        Returns:
            添加的文档ID列表
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        doc_ids = []
        now = datetime.now()
        
        for doc in documents:
            # 生成嵌入向量
            if doc.embedding is None:
                doc.embedding = self.embedding_model.encode(doc.content)
            
            embedding_str = json.dumps(doc.embedding)
            metadata_str = json.dumps(doc.metadata)
            
            cursor.execute("""
                INSERT OR REPLACE INTO documents
                (id, content, metadata, embedding, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                doc.doc_id,
                doc.content,
                metadata_str,
                embedding_str,
                now,
                now,
            ))
            
            doc_ids.append(doc.doc_id)
        
        conn.commit()
        conn.close()
        
        logger.info(f"Added {len(documents)} documents to vector store")
        return doc_ids
    
    def search(
        self,
        query: str,
        k: int = 5,
        threshold: float = 0.5,
    ) -> List[Tuple[Document, float]]:
        """
        搜索相似的文档
        
        Args:
            query: 查询文本
            k: 返回文档数
            threshold: 相似度阈值
            
        Returns:
            (文档, 相似度)元组列表
        """
        # 获取查询的嵌入向量
        query_embedding = self.embedding_model.encode(query)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, content, metadata, embedding
            FROM documents
            ORDER BY created_at DESC
            LIMIT 100
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        # 计算相似度并排序
        results = []
        for row in rows:
            doc_id, content, metadata_str, embedding_str = row
            embedding = json.loads(embedding_str)
            
            similarity = self.embedding_model.similarity(
                query_embedding,
                embedding,
            )
            
            if similarity >= threshold:
                doc = Document(
                    doc_id=doc_id,
                    content=content,
                    metadata=json.loads(metadata_str),
                    embedding=embedding,
                )
                results.append((doc, similarity))
        
        # 按相似度排序
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results[:k]
    
    def get_document(self, doc_id: str) -> Optional[Document]:
        """获取单个文档"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, content, metadata, embedding
            FROM documents
            WHERE id = ?
        """, (doc_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            doc_id, content, metadata_str, embedding_str = row
            return Document(
                doc_id=doc_id,
                content=content,
                metadata=json.loads(metadata_str),
                embedding=json.loads(embedding_str),
            )
        return None
    
    def delete_document(self, doc_id: str) -> bool:
        """删除文档"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Deleted document {doc_id}")
        return True
    
    def get_all_documents(self, limit: int = 100) -> List[Document]:
        """获取所有文档"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, content, metadata, embedding
            FROM documents
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        documents = []
        for row in rows:
            doc_id, content, metadata_str, embedding_str = row
            doc = Document(
                doc_id=doc_id,
                content=content,
                metadata=json.loads(metadata_str),
                embedding=json.loads(embedding_str),
            )
            documents.append(doc)
        
        return documents
    
    def clear_all(self) -> None:
        """清空所有文档"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM documents")
        conn.commit()
        conn.close()
        logger.info("Cleared all documents from vector store")


class RAGRetriever:
    """RAG检索器 - 管理文档检索和上下文生成"""
    
    def __init__(self, vector_store: Optional[VectorStore] = None):
        """初始化RAG检索器"""
        self.vector_store = vector_store or VectorStore()
    
    def add_knowledge_base(
        self,
        documents: List[str],
        metadata_list: Optional[List[Dict[str, Any]]] = None,
    ) -> List[str]:
        """
        添加知识库文档
        
        Args:
            documents: 文档内容列表
            metadata_list: 元数据列表
            
        Returns:
            添加的文档ID列表
        """
        import uuid
        
        doc_objects = []
        for i, content in enumerate(documents):
            doc_id = str(uuid.uuid4())
            metadata = metadata_list[i] if metadata_list else {}
            doc = Document(
                doc_id=doc_id,
                content=content,
                metadata=metadata,
            )
            doc_objects.append(doc)
        
        return self.vector_store.add_documents(doc_objects)
    
    def retrieve(
        self,
        query: str,
        k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        检索相关文档
        
        Args:
            query: 查询文本
            k: 返回文档数
            
        Returns:
            文档列表
        """
        results = self.vector_store.search(
            query=query,
            k=k,
            threshold=config.SIMILARITY_THRESHOLD,
        )
        
        return [
            {
                "content": doc.content,
                "metadata": doc.metadata,
                "similarity": float(similarity),
            }
            for doc, similarity in results
        ]
    
    def build_context(self, query: str, k: int = 3) -> str:
        """
        构建RAG上下文
        
        Args:
            query: 查询文本
            k: 检索文档数
            
        Returns:
            格式化的上下文
        """
        retrieved_docs = self.retrieve(query, k=k)
        
        if not retrieved_docs:
            return "No relevant documents found in the knowledge base."
        
        context = "Relevant documents from knowledge base:\n\n"
        for i, doc in enumerate(retrieved_docs, 1):
            context += f"[Document {i}]\n"
            context += f"Content: {doc['content'][:500]}\n"
            context += f"Relevance Score: {doc['similarity']:.2f}\n\n"
        
        return context
