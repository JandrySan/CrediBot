from sqlalchemy.orm import Session
from app.models.customer import Customer


class CustomerRepository:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _normalize_phone(phone_number: str) -> str:
        value = (phone_number or "").strip()
        if not value:
            return ""

        if value.startswith("whatsapp:"):
            value = value.split(":", 1)[1]

        if value.startswith("+"):
            return value

        if value.startswith("00"):
            return f"+{value[2:]}"

        return f"+{value}"

    def get_by_phone(self, phone_number: str):
        normalized = self._normalize_phone(phone_number)
        legacy = f"whatsapp:{normalized}"

        return (
            self.db.query(Customer)
            .filter(Customer.phone_number.in_([normalized, legacy, phone_number]))
            .first()
        )

    def get_or_create(self, phone_number: str):
        customer = self.get_by_phone(phone_number)

        if customer:
            if customer.phone_number != self._normalize_phone(phone_number):
                customer.phone_number = self._normalize_phone(phone_number)
                self.db.commit()
                self.db.refresh(customer)
            return customer

        customer = Customer(phone_number=self._normalize_phone(phone_number))
        self.db.add(customer)
        self.db.commit()
        self.db.refresh(customer)

        return customer