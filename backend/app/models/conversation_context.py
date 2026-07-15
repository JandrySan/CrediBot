from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class ConversationContext(Base):
    __tablename__ = "conversation_contexts"

    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), unique=True, index=True
    )
    active_goal: Mapped[str] = mapped_column(
        String(50), default="CREDIT_PREQUALIFICATION", server_default="CREDIT_PREQUALIFICATION"
    )
    pending_field: Mapped[str | None] = mapped_column(String(60))
    last_intent: Mapped[str | None] = mapped_column(String(50))
    slots: Mapped[dict] = mapped_column(JSON, default=dict, server_default="{}")
    revision: Mapped[int] = mapped_column(default=1, server_default="1")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
