import csv
import io
import json
from typing import Any

from sqlalchemy.orm import Session

from app.services.rag.models import KnowledgeBase


class FAQLoader:
    def __init__(self, db: Session):
        self.db = db

    def load_json(self, raw_content: str) -> dict:
        data = json.loads(raw_content)
        rows = data.get("faqs") if isinstance(data, dict) else data

        if not isinstance(rows, list):
            raise ValueError("El JSON debe ser una lista o un objeto con la clave 'faqs'.")

        return self._load_rows(rows)

    def load_csv(self, raw_content: str) -> dict:
        reader = csv.DictReader(io.StringIO(raw_content))
        return self._load_rows(list(reader))

    def _load_rows(self, rows: list[dict[str, Any]]) -> dict:
        created = 0
        skipped = 0
        errors: list[dict[str, Any]] = []

        for index, row in enumerate(rows, start=1):
            try:
                question = str(row.get("question") or row.get("pregunta") or "").strip()
                answer = str(row.get("answer") or row.get("respuesta") or "").strip()
                category = str(row.get("category") or row.get("categoria") or "").strip() or None
                keywords = self._normalize_keywords(
                    row.get("keywords") or row.get("palabras_clave") or []
                )

                if not question or not answer:
                    skipped += 1
                    errors.append(
                        {
                            "row": index,
                            "error": "question/answer son obligatorios",
                        }
                    )
                    continue

                faq = KnowledgeBase(
                    question=question,
                    answer=answer,
                    category=category,
                    is_active=True,
                )
                faq.set_keywords(keywords or self._keywords_from_text(question))

                self.db.add(faq)
                created += 1
            except (AttributeError, TypeError, ValueError) as exc:
                skipped += 1
                errors.append({"row": index, "error": str(exc)})

        self.db.flush()

        return {
            "created": created,
            "skipped": skipped,
            "errors": errors,
        }

    def _normalize_keywords(self, value: Any) -> list[str]:
        if isinstance(value, list):
            items = value
        elif isinstance(value, str):
            value = value.strip()
            if not value:
                items = []
            else:
                try:
                    parsed = json.loads(value)
                    items = parsed if isinstance(parsed, list) else value.split(",")
                except json.JSONDecodeError:
                    items = value.split(",")
        else:
            items = []

        clean_keywords: list[str] = []
        for item in items:
            keyword = str(item).strip().lower()
            if keyword and keyword not in clean_keywords:
                clean_keywords.append(keyword)

        return clean_keywords

    def _keywords_from_text(self, text: str) -> list[str]:
        stopwords = {"para", "como", "cual", "cuales", "que", "los", "las", "una", "con"}
        words = [token.strip(".,;:!?¿¡()[]").lower() for token in text.split()]
        return [word for word in words if len(word) > 3 and word not in stopwords][:12]
