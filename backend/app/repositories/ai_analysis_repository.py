import json
from sqlalchemy.orm import Session

from app.models.ai_analysis import AIAnalysis


class AIAnalysisRepository:
    def __init__(self, db: Session):
        self.db = db

    def save_analysis(
        self,
        conversation_id: int,
        intent: str | None,
        extracted_data: dict,
        model_used: str | None = None
    ):
        analysis = AIAnalysis(
            conversation_id=conversation_id,
            intent=intent,
            extracted_data=json.dumps(extracted_data, ensure_ascii=False),
            model_used=model_used
        )

        self.db.add(analysis)
        self.db.commit()
        self.db.refresh(analysis)

        return analysis