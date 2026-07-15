from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class CustomerFinancialProfile(Base):
    __tablename__ = "customer_financial_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE"), unique=True, index=True
    )
    employment_status: Mapped[str | None] = mapped_column(String(30))
    occupation: Mapped[str | None] = mapped_column(String(120))
    employer_name: Mapped[str | None] = mapped_column(String(140))
    economic_activity: Mapped[str | None] = mapped_column(String(140))
    job_tenure_months: Mapped[int | None]
    business_tenure_months: Mapped[int | None]
    monthly_net_income: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    other_monthly_income: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    monthly_living_expenses: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    existing_monthly_debt_payments: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    dependent_count: Mapped[int | None]
    housing_status: Mapped[str | None] = mapped_column(String(30))
    assets_total: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    liabilities_total: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    source_of_funds: Mapped[str | None] = mapped_column(Text)
    pep_status: Mapped[str] = mapped_column(String(20), default="UNKNOWN", server_default="UNKNOWN")
    identity_verification_status: Mapped[str] = mapped_column(
        String(20), default="PENDING", server_default="PENDING"
    )
    income_verification_status: Mapped[str] = mapped_column(
        String(20), default="DECLARED", server_default="DECLARED"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
