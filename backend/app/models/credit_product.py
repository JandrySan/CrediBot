from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class CreditProduct(Base):
    __tablename__ = "credit_products"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    segment: Mapped[str] = mapped_column(String(50), index=True)
    description: Mapped[str] = mapped_column(Text)
    currency: Mapped[str] = mapped_column(String(3), default="USD", server_default="USD")
    min_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    max_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    min_term_months: Mapped[int]
    max_term_months: Mapped[int]
    effective_annual_rate: Mapped[Decimal] = mapped_column(Numeric(8, 4))
    max_effective_annual_rate: Mapped[Decimal] = mapped_column(Numeric(8, 4))
    amortization_type: Mapped[str] = mapped_column(
        String(20), default="FRENCH", server_default="FRENCH"
    )
    payment_frequency: Mapped[str] = mapped_column(
        String(20), default="MONTHLY", server_default="MONTHLY"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    is_demo: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    source_url: Mapped[str | None] = mapped_column(Text)
    effective_from: Mapped[date] = mapped_column(Date)
    effective_to: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )

    requirements: Mapped[list[CreditProductRequirement]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )


class CreditProductRequirement(Base):
    __tablename__ = "credit_product_requirements"
    __table_args__ = (UniqueConstraint("product_id", "code", name="uq_product_requirement_code"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("credit_products.id", ondelete="CASCADE"), index=True
    )
    code: Mapped[str] = mapped_column(String(60))
    name: Mapped[str] = mapped_column(String(140))
    description: Mapped[str] = mapped_column(Text)
    applicant_type: Mapped[str] = mapped_column(
        String(30), default="ALL", server_default="ALL", index=True
    )
    requirement_type: Mapped[str] = mapped_column(String(30))
    stage: Mapped[str] = mapped_column(String(30), default="APPLICATION")
    is_required: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    conditions: Mapped[dict] = mapped_column(JSON, default=dict, server_default="{}")
    display_order: Mapped[int] = mapped_column(default=0, server_default="0")

    product: Mapped[CreditProduct] = relationship(back_populates="requirements")
