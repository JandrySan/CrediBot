from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class CreditDecision(Base):
    __tablename__ = "credit_decisions"

    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int] = mapped_column(
        ForeignKey("credit_applications.id", ondelete="CASCADE"), index=True
    )
    product_id: Mapped[int] = mapped_column(ForeignKey("credit_products.id"), index=True)
    policy_version_id: Mapped[int] = mapped_column(
        ForeignKey("credit_policy_versions.id"), index=True
    )
    result: Mapped[str] = mapped_column(String(30), index=True)
    is_final_decision: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    requested_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    proposed_term_months: Mapped[int]
    estimated_installment: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    verified_monthly_income: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    monthly_living_expenses: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    existing_monthly_debt_payments: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    disposable_income: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    current_dti: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    projected_dti: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    credit_score: Mapped[int | None]
    risk_level: Mapped[str | None] = mapped_column(String(20))
    reason_codes: Mapped[list] = mapped_column(JSON, default=list, server_default="[]")
    missing_requirements: Mapped[list] = mapped_column(JSON, default=list, server_default="[]")
    input_snapshot: Mapped[dict] = mapped_column(JSON, default=dict, server_default="{}")
    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
