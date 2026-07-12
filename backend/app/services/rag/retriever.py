from app.services.rag.embeddings import EmbeddingService
from app.services.rag.vector_store import VectorStore


class Retriever:
    def __init__(self, embedding_service: EmbeddingService, vector_store: VectorStore):
        self.embedding_service = embedding_service
        self.vector_store = vector_store

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        query_embedding = self.embedding_service.embed(query)
        return self.vector_store.search(query_embedding, top_k=top_k)

    def format_context(self, results: list[dict], max_chars: int = 2000) -> str:
        parts = []
        total = 0
        for r in results:
            snippet = r["content"].strip()
            if total + len(snippet) > max_chars:
                remaining = max_chars - total
                if remaining > 50:
                    parts.append(snippet[:remaining] + "...")
                break
            parts.append(snippet)
            total += len(snippet)
        return "\n\n---\n\n".join(parts)
