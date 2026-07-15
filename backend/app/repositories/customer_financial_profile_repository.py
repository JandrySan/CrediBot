from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.customer_financial_profile import CustomerFinancialProfile


class CustomerFinancialProfileRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_or_create(self, customer_id: int) -> CustomerFinancialProfile:
        profile = self.db.scalar(
            select(CustomerFinancialProfile).where(
                CustomerFinancialProfile.customer_id == customer_id
            )
        )
        if profile:
            return profile

        profile = CustomerFinancialProfile(customer_id=customer_id)
        self.db.add(profile)
        self.db.flush()
        self.db.refresh(profile)
        return profile

    def update(self, profile: CustomerFinancialProfile, **values):
        for field, value in values.items():
            if hasattr(profile, field):
                setattr(profile, field, value)
        self.db.flush()
        return profile
