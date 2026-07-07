from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func

from app.database.base import Base


class ConversationStateHistory(Base):
    __tablename__ = "conversation_state_history"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)

    previous_state = Column(String(50), nullable=True)
    new_state = Column(String(50), nullable=False)
    reason = Column(String(255), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())