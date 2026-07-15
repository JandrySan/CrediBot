from sqlalchemy.orm import Session

from app.models.credit_application import CreditApplication


class CreditApplicationRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_latest_by_customer(self, customer_id: int):
        return (
            self.db.query(CreditApplication)
            .filter(CreditApplication.customer_id == customer_id)
            .order_by(CreditApplication.id.desc())
            .first()
        )

    def get_or_create_latest(self, customer_id: int):
        application = self.get_latest_by_customer(customer_id)

        if application and application.result is None:
            return application

        application = CreditApplication(customer_id=customer_id)
        self.db.add(application)
        self.db.flush()
        self.db.refresh(application)

        return application

    def update(self, application: CreditApplication, **kwargs):
        for key, value in kwargs.items():
            setattr(application, key, value)

        self.db.flush()
        self.db.refresh(application)

        return application
