from sqlalchemy.orm import Session

from app.schemas.dashboard import FAQItem
from app.services.rag.faq_loader import FAQLoader
from app.services.rag.models import KnowledgeBase


class FAQAdminService:
    def __init__(self, db: Session):
        self.db = db

    def upload(self, filename: str, raw_content: str) -> dict:
        loader = FAQLoader(self.db)
        result = (
            loader.load_csv(raw_content)
            if filename.lower().endswith(".csv")
            else loader.load_json(raw_content)
        )
        return {
            "success": True,
            "message": "FAQs cargadas correctamente",
            **result,
        }

    def list_active(self) -> list[FAQItem]:
        rows = (
            self.db.query(KnowledgeBase)
            .filter(KnowledgeBase.is_active.is_(True))
            .order_by(KnowledgeBase.id.desc())
            .all()
        )
        return [self._serialize(faq) for faq in rows]

    def delete(self, faq_id: int) -> dict:
        faq = self.db.get(KnowledgeBase, faq_id)
        if not faq:
            return {"success": False, "message": "FAQ no encontrada"}

        faq.is_active = False
        self.db.flush()
        return {"success": True, "message": "FAQ eliminada", "faq_id": faq_id}

    @staticmethod
    def _serialize(faq: KnowledgeBase) -> FAQItem:
        return FAQItem(
            id=faq.id,
            question=faq.question,
            answer=faq.answer,
            category=faq.category,
            keywords=faq.keyword_list(),
            is_active=faq.is_active,
            created_at=faq.created_at,
            updated_at=faq.updated_at,
        )
