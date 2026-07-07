from decimal import Decimal

from app.services.rules.credit_rule_engine import CreditRuleEngine


class CreditApplicationService:
    def __init__(self):
        self.rule_engine = CreditRuleEngine()

    def apply_extracted_data(self, customer, application, data: dict, db):
        if data.get("full_name") and not customer.full_name:
            customer.full_name = data["full_name"]

        if data.get("amount") and application.amount is None:
            application.amount = Decimal(str(data["amount"]))

        if data.get("term_months") and application.term_months is None:
            application.term_months = int(data["term_months"])

        if data.get("monthly_income") and application.monthly_income is None:
            application.monthly_income = Decimal(str(data["monthly_income"]))

        db.commit()

    def evaluate_if_complete(self, application):
        if (
            not application.amount
            or not application.term_months
            or not application.monthly_income
            or application.result
        ):
            return None

        return self.rule_engine.evaluate(
            amount=Decimal(application.amount),
            term_months=application.term_months,
            monthly_income=Decimal(application.monthly_income)
        )