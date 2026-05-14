"""
RAG retrieval with real embeddings and a local Qdrant vector store.

The dense retrieval stack is:
- chunk documents
- embed chunks with a configurable embedding provider
- store vectors in local Qdrant
- embed queries and search by vector similarity
- apply a small lexical bonus for better exact-match precision
"""
import logging
import re
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, Sequence

from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models

from app.config.config import get_config

logger = logging.getLogger(__name__)
config = get_config()


def _tokenize(text: str) -> List[str]:
    return re.findall(r"\w+", text.lower())


class EmbeddingProvider(Protocol):
    """Embedding provider interface used by the vector store."""

    def embed_texts(self, texts: Sequence[str]) -> List[List[float]]:
        ...

    def embed_query(self, text: str) -> List[float]:
        ...

    @property
    def dimension(self) -> int:
        ...


class OpenAIEmbeddingProvider:
    """OpenAI embeddings backed by a real embedding model."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        dimensions: Optional[int] = None,
    ):
        self.api_key = api_key or config.OPENAI_API_KEY
        self.model = model or config.EMBEDDING_MODEL
        self.dimensions = dimensions or config.EMBEDDING_DIMENSIONS
        self._dimension = self.dimensions
        self._client: Optional[OpenAI] = None

        if self.api_key:
            self._client = OpenAI(api_key=self.api_key)

    @property
    def dimension(self) -> int:
        if self._dimension is None:
            raise RuntimeError(
                "Embedding dimension is unknown. Configure EMBEDDING_DIMENSIONS."
            )
        return self._dimension

    def embed_texts(self, texts: Sequence[str]) -> List[List[float]]:
        if not texts:
            return []
        if self._client is None:
            raise RuntimeError("OPENAI_API_KEY is not configured.")

        request_args: Dict[str, Any] = {
            "model": self.model,
            "input": list(texts),
        }
        if self.dimensions is not None:
            request_args["dimensions"] = self.dimensions

        response = self._client.embeddings.create(**request_args)
        vectors = [item.embedding for item in response.data]
        if vectors and self._dimension is None:
            self._dimension = len(vectors[0])
        return vectors

    def embed_query(self, text: str) -> List[float]:
        return self.embed_texts([text])[0]


class FakeEmbeddingProvider:
    """Deterministic embedding provider used in tests."""

    def __init__(self, dimension: int = 32):
        self._dimension = dimension

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed_texts(self, texts: Sequence[str]) -> List[List[float]]:
        vectors: List[List[float]] = []
        for text in texts:
            vector = [0.0] * self._dimension
            for token in _tokenize(text):
                index = hash(token) % self._dimension
                vector[index] += 1.0
            norm = sum(value * value for value in vector) ** 0.5
            if norm:
                vector = [value / norm for value in vector]
            vectors.append(vector)
        return vectors

    def embed_query(self, text: str) -> List[float]:
        return self.embed_texts([text])[0]


@dataclass
class DocumentChunk:
    chunk_id: str
    document_id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    token_count: int = 0

    def to_payload(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "content": self.content,
            "metadata": self.metadata,
            "token_count": self.token_count,
        }


class TextChunker:
    """Simple word-based chunking with overlap."""

    def __init__(self, chunk_size: int, chunk_overlap: int):
        self.chunk_size = max(chunk_size, 50)
        self.chunk_overlap = max(min(chunk_overlap, self.chunk_size - 1), 0)

    def split_text(self, text: str) -> List[str]:
        words = text.split()
        if not words:
            return []

        chunks: List[str] = []
        step = max(self.chunk_size - self.chunk_overlap, 1)
        for start in range(0, len(words), step):
            chunk_words = words[start : start + self.chunk_size]
            if not chunk_words:
                continue
            chunks.append(" ".join(chunk_words))
            if start + self.chunk_size >= len(words):
                break
        return chunks


class VectorStore:
    """Qdrant-backed vector store with local persistence."""

    def __init__(
        self,
        collection_name: Optional[str] = None,
        qdrant_path: Optional[str] = None,
        embedding_provider: Optional[EmbeddingProvider] = None,
    ):
        self.collection_name = collection_name or config.QDRANT_COLLECTION_NAME
        self.qdrant_path = qdrant_path or config.QDRANT_PATH
        self.embedding_provider = embedding_provider or OpenAIEmbeddingProvider()
        self.chunker = TextChunker(
            chunk_size=config.CHUNK_SIZE,
            chunk_overlap=config.CHUNK_OVERLAP,
        )

        if self.qdrant_path != ":memory:":
            Path(self.qdrant_path).mkdir(parents=True, exist_ok=True)
            self.client = QdrantClient(path=self.qdrant_path)
        else:
            self.client = QdrantClient(location=":memory:")

        self._ensure_collection()

    def close(self) -> None:
        """Release local Qdrant resources, especially important on Windows."""
        self.client.close()

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass

    def _ensure_collection(self) -> None:
        collections = self.client.get_collections().collections
        exists = any(collection.name == self.collection_name for collection in collections)
        if exists:
            return

        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=qdrant_models.VectorParams(
                size=self.embedding_provider.dimension,
                distance=qdrant_models.Distance.COSINE,
            ),
        )
        logger.info(
            "Created Qdrant collection %s at %s",
            self.collection_name,
            self.qdrant_path,
        )

    def add_documents(
        self,
        documents: List[str],
        metadata_list: Optional[List[Dict[str, Any]]] = None,
    ) -> List[str]:
        chunks: List[DocumentChunk] = []
        doc_ids: List[str] = []

        for index, document in enumerate(documents):
            metadata = dict(metadata_list[index]) if metadata_list else {}
            document_id = str(uuid.uuid4())
            doc_ids.append(document_id)

            for chunk_text in self.chunker.split_text(document):
                chunk_id = str(uuid.uuid4())
                chunk_metadata = dict(metadata)
                chunk_metadata.setdefault("document_position", index)
                chunks.append(
                    DocumentChunk(
                        chunk_id=chunk_id,
                        document_id=document_id,
                        content=chunk_text,
                        metadata=chunk_metadata,
                        token_count=len(chunk_text.split()),
                    )
                )

        if not chunks:
            return doc_ids

        vectors = self.embedding_provider.embed_texts([chunk.content for chunk in chunks])
        points = [
            qdrant_models.PointStruct(
                id=chunk.chunk_id,
                vector=vector,
                payload=chunk.to_payload(),
            )
            for chunk, vector in zip(chunks, vectors)
        ]

        self.client.upsert(collection_name=self.collection_name, points=points)
        logger.info("Added %s chunks into Qdrant collection %s", len(points), self.collection_name)
        return doc_ids

    def search(
        self,
        query: str,
        k: int = 5,
        threshold: float = 0.25,
    ) -> List[Dict[str, Any]]:
        query_vector = self.embedding_provider.embed_query(query)
        response = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=max(k * config.RAG_CANDIDATE_MULTIPLIER, k),
            with_payload=True,
        )
        candidates = response.points

        query_tokens = set(_tokenize(query))
        ranked: List[Dict[str, Any]] = []
        for candidate in candidates:
            payload = candidate.payload or {}
            content = payload.get("content", "")
            lexical_score = self._keyword_overlap(query_tokens, set(_tokenize(content)))
            dense_score = float(candidate.score or 0.0)
            final_score = dense_score * config.DENSE_SCORE_WEIGHT + lexical_score * (
                1.0 - config.DENSE_SCORE_WEIGHT
            )
            if final_score < threshold:
                continue

            ranked.append(
                {
                    "content": content,
                    "metadata": payload.get("metadata", {}),
                    "document_id": payload.get("document_id"),
                    "chunk_id": payload.get("chunk_id", str(candidate.id)),
                    "score": final_score,
                    "dense_score": dense_score,
                    "lexical_score": lexical_score,
                }
            )

        ranked.sort(key=lambda item: item["score"], reverse=True)
        return ranked[:k]

    def clear_all(self) -> None:
        self.client.delete_collection(collection_name=self.collection_name)
        self._ensure_collection()

    @staticmethod
    def _keyword_overlap(left: set[str], right: set[str]) -> float:
        if not left or not right:
            return 0.0
        return len(left & right) / len(left | right)


class RAGRetriever:
    """Knowledge retrieval facade used by the agent."""

    def __init__(self, vector_store: Optional[VectorStore] = None):
        self.vector_store = vector_store or VectorStore()

    def add_knowledge_base(
        self,
        documents: List[str],
        metadata_list: Optional[List[Dict[str, Any]]] = None,
    ) -> List[str]:
        return self.vector_store.add_documents(documents, metadata_list)

    def retrieve(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        return self.vector_store.search(
            query=query,
            k=k,
            threshold=config.SIMILARITY_THRESHOLD,
        )

    def build_context(self, query: str, k: int = 3) -> str:
        chunks = self.retrieve(query=query, k=k)
        if not chunks:
            return "No relevant knowledge base context was found."

        lines = ["Relevant knowledge base context:"]
        for index, chunk in enumerate(chunks, start=1):
            source = chunk["metadata"].get("source", f"document-{index}")
            lines.append(
                f"[Chunk {index}] source={source} score={chunk['score']:.2f}\n"
                f"{chunk['content'][:600]}"
            )
        return "\n\n".join(lines)
