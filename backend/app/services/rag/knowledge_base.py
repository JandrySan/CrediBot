import re
from pathlib import Path

from sqlalchemy.orm import Session

from app.services.rag.embeddings import EmbeddingService
from app.services.rag.vector_store import VectorStore
from app.services.rag.retriever import Retriever


class KnowledgeBase:
    def __init__(self, db: Session):
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStore(db)
        self.retriever = Retriever(self.embedding_service, self.vector_store)

    def ingest_faq_file(self, file_path: str | Path):
        path = Path(file_path)
        content = path.read_text(encoding="utf-8")
        chunks = self._chunk_faq_markdown(content)
        embeddings = self.embedding_service.embed_batch([c[0] for c in chunks])

        data = []
        for (text, meta), emb in zip(chunks, embeddings):
            data.append((text, emb, meta))

        self.vector_store.insert_chunks(data)
        return len(data)

    def query(self, question: str, top_k: int = 3) -> str:
        results = self.retriever.search(question, top_k=top_k)
        if not results:
            return ""
        return self.retriever.format_context(results)

    def is_ready(self) -> bool:
        return self.vector_store.count() > 0

    def _chunk_faq_markdown(self, content: str) -> list[tuple[str, dict]]:
        chunks = []
        lines = content.split("\n")
        current_section = "General"
        current_q = None
        current_lines: list[str] = []

        def flush_qa():
            if current_q is not None and current_lines:
                text = " ".join(current_lines).strip()
                if text:
                    chunks.append((text, {"section": current_section, "question": current_q}))
                current_lines.clear()

        for line in lines:
            if line.startswith("# "):
                flush_qa()
                current_section = line[2:].strip()
                current_q = None
            elif line.startswith("## "):
                flush_qa()
                current_q = line[3:].strip()
            elif line.strip():
                current_lines.append(line.strip())
            else:
                if current_q and current_lines:
                    flush_qa()

        flush_qa()
        return chunks
