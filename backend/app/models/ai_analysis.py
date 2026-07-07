from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func

from app.database.base import Base


class AIAnalysis(Base):
    __tablename__ = "ai_analysis"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)

    intent = Column(String(50), nullable=True)
    extracted_data = Column(Text, nullable=True)
    model_used = Column(String(100), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())