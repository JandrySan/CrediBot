from sqlalchemy.orm import Session
from app.models.customer import Customer


class CustomerRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_phone(self, phone_number: str):
        return (
            self.db.query(Customer)
            .filter(Customer.phone_number == phone_number)
            .first()
        )

    def get_or_create(self, phone_number: str):
        customer = self.get_by_phone(phone_number)

        if customer:
            return customer

        customer = Customer(phone_number=phone_number)
        self.db.add(customer)
        self.db.commit()
        self.db.refresh(customer)

        return customer