import json
import math
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.document_chunk import DocumentChunk


class VectorStore:
    def __init__(self, db: Session):
        self.db = db
        self._pgvector_available = self._check_pgvector()

    def _check_pgvector(self) -> bool:
        try:
            result = self.db.execute(
                text("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
            ).scalar()
            return bool(result)
        except Exception:
            return False

    def enable_extension(self):
        try:
            self.db.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            self.db.commit()
            self._pgvector_available = True
        except Exception:
            self._pgvector_available = False

    def insert_chunks(self, chunks: list[tuple[str, list[float], dict]]):
        for content, embedding, source_info in chunks:
            doc = DocumentChunk(
                content=content,
                embedding=json.dumps(embedding),
                source_info=json.dumps(source_info, default=str),
            )
            self.db.add(doc)
        self.db.commit()

    def search(self, query_embedding: list[float], top_k: int = 5) -> list[dict]:
        all_chunks = (
            self.db.query(DocumentChunk)
            .filter(DocumentChunk.embedding.isnot(None))
            .all()
        )

        scored = []
        for chunk in all_chunks:
            stored = json.loads(chunk.embedding)
            score = self._cosine_similarity(query_embedding, stored)
            scored.append({
                "id": chunk.id,
                "content": chunk.content,
                "source_info": json.loads(chunk.source_info) if chunk.source_info else {},
                "score": score,
            })

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]

    def count(self) -> int:
        return self.db.query(DocumentChunk).count()

    def clear(self):
        self.db.query(DocumentChunk).delete()
        self.db.commit()

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        dot = sum(av * bv for av, bv in zip(a, b))
        norm_a = math.sqrt(sum(av * av for av in a))
        norm_b = math.sqrt(sum(bv * bv for bv in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)
