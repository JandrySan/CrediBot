from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class CreditApplication(Base):
    __tablename__ = "credit_applications"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)

    credit_type = Column(String(50), nullable=True)
    amount = Column(Numeric(12, 2), nullable=True)
    term_months = Column(Integer, nullable=True)
    monthly_income = Column(Numeric(12, 2), nullable=True)

    result = Column(String(50), nullable=True)
    reason = Column(String(255), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    customer = relationship("Customer", back_populates="credit_applications")