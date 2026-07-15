import re
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.services.ai.ai_gateway import AIGateway
from app.services.rag.models import KnowledgeBase


@dataclass
class FAQMatch:
    faq: KnowledgeBase
    score: int


class RetrievalService:
    def __init__(self, db: Session):
        self.db = db
        self.ai = AIGateway()

    def search(self, query: str, limit: int = 5) -> list[KnowledgeBase]:
        candidates = self._keyword_search(query=query, limit=limit)
        if len(candidates) <= 1:
            return [match.faq for match in candidates]

        reranked = self._rerank_with_llm(query, [match.faq for match in candidates])
        return reranked or [match.faq for match in candidates]

    def best_match(self, query: str) -> KnowledgeBase | None:
        results = self.search(query=query, limit=5)
        return results[0] if results else None

    def build_context(self, query: str, limit: int = 3) -> str:
        results = self.search(query=query, limit=limit)
        if not results:
            return ""

        blocks = []
        for index, faq in enumerate(results, start=1):
            blocks.append(f"FAQ {index}\nPregunta: {faq.question}\nRespuesta: {faq.answer}")

        return "\n\n".join(blocks)

    def _keyword_search(self, query: str, limit: int) -> list[FAQMatch]:
        query_tokens = set(self._tokens(query))
        if not query_tokens:
            return []

        rows = (
            self.db.query(KnowledgeBase)
            .filter(KnowledgeBase.is_active.is_(True))
            .order_by(KnowledgeBase.id.desc())
            .all()
        )

        matches: list[FAQMatch] = []
        for faq in rows:
            faq_tokens = set(self._tokens(f"{faq.question} {faq.answer}"))
            keyword_tokens = set(faq.keyword_list())

            keyword_score = len(query_tokens.intersection(keyword_tokens)) * 3
            text_score = len(query_tokens.intersection(faq_tokens))
            score = keyword_score + text_score

            if score > 0:
                matches.append(FAQMatch(faq=faq, score=score))

        matches.sort(key=lambda item: (item.score, item.faq.id), reverse=True)
        return matches[:limit]

    def _rerank_with_llm(
        self,
        query: str,
        candidates: list[KnowledgeBase],
    ) -> list[KnowledgeBase]:
        if not self.ai.is_available():
            return []

        candidate_text = "\n".join(
            f"{faq.id}. {faq.question}\nRespuesta: {faq.answer}" for faq in candidates
        )

        result = self.ai.generate_json(
            system_prompt=(
                "Eres un reranker de FAQs. Devuelve JSON valido con la clave "
                "'ordered_ids', una lista de ids ordenados por relevancia para la consulta."
            ),
            user_prompt=(
                f"Consulta del usuario:\n{query}\n\n"
                f"FAQs candidatas:\n{candidate_text}\n\n"
                '{"ordered_ids": [1, 2, 3]}'
            ),
        )

        ordered_ids = result.get("ordered_ids")
        if not isinstance(ordered_ids, list):
            return []

        by_id = {faq.id: faq for faq in candidates}
        reranked: list[KnowledgeBase] = []
        for raw_id in ordered_ids:
            try:
                faq_id = int(raw_id)
            except (TypeError, ValueError):
                continue

            faq = by_id.get(faq_id)
            if faq and faq not in reranked:
                reranked.append(faq)

        for faq in candidates:
            if faq not in reranked:
                reranked.append(faq)

        return reranked

    def _tokens(self, text: str) -> list[str]:
        normalized = (text or "").lower()
        normalized = normalized.replace("á", "a").replace("é", "e")
        normalized = normalized.replace("í", "i").replace("ó", "o").replace("ú", "u")
        raw_tokens = re.findall(r"[a-z0-9]+", normalized)
        stopwords = {
            "para",
            "como",
            "cual",
            "cuales",
            "que",
            "los",
            "las",
            "una",
            "con",
            "por",
            "del",
            "tengo",
            "quiero",
            "puedo",
            "necesito",
            "sobre",
        }
        return [token for token in raw_tokens if len(token) > 2 and token not in stopwords]
