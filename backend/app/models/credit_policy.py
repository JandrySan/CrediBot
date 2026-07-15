from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import JSON, Boolean, Date, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class CreditPolicyVersion(Base):
    __tablename__ = "credit_policy_versions"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(60), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(140))
    status: Mapped[str] = mapped_column(String(20), default="DRAFT", index=True)
    description: Mapped[str] = mapped_column(Text)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    effective_from: Mapped[date] = mapped_column(Date)
    effective_to: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    rules: Mapped[list[CreditPolicyRule]] = relationship(
        back_populates="policy_version", cascade="all, delete-orphan"
    )


class CreditPolicyRule(Base):
    __tablename__ = "credit_policy_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    policy_version_id: Mapped[int] = mapped_column(
        ForeignKey("credit_policy_versions.id", ondelete="CASCADE"), index=True
    )
    product_id: Mapped[int | None] = mapped_column(
        ForeignKey("credit_products.id", ondelete="CASCADE"), index=True
    )
    code: Mapped[str] = mapped_column(String(80), index=True)
    category: Mapped[str] = mapped_column(String(40), index=True)
    parameters: Mapped[dict] = mapped_column(JSON, default=dict, server_default="{}")
    severity: Mapped[str] = mapped_column(String(20), default="BLOCKING")
    outcome_on_failure: Mapped[str] = mapped_column(String(30))
    explanation: Mapped[str] = mapped_column(Text)
    display_order: Mapped[int] = mapped_column(default=0, server_default="0")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    policy_version: Mapped[CreditPolicyVersion] = relationship(back_populates="rules")
