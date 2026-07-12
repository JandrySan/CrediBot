import json

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from app.database.base import Base


class KnowledgeBase(Base):
    __tablename__ = "knowledge_base"

    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    category = Column(String(80), nullable=True, index=True)
    keywords = Column(Text, nullable=False, default="[]")
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def keyword_list(self) -> list[str]:
        try:
            value = json.loads(self.keywords or "[]")
        except json.JSONDecodeError:
            return []

        if not isinstance(value, list):
            return []

        return [str(item).strip().lower() for item in value if str(item).strip()]

    def set_keywords(self, keywords: list[str] | None):
        clean_keywords = []
        for keyword in keywords or []:
            value = str(keyword).strip().lower()
            if value and value not in clean_keywords:
                clean_keywords.append(value)

        self.keywords = json.dumps(clean_keywords, ensure_ascii=False)

