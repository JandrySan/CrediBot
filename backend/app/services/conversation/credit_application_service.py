from decimal import Decimal

from app.services.credit_bureau.profile_service import (
    CreditBureauProfileService,
    CreditBureauUnavailable,
)
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

    def evaluate_if_complete(self, application, customer=None, db=None):
        if (
            not application.amount
            or not application.term_months
            or not application.monthly_income
            or application.result
        ):
            return None

        evaluation = self.rule_engine.evaluate(
            amount=Decimal(application.amount),
            term_months=application.term_months,
            monthly_income=Decimal(application.monthly_income)
        )

        bureau_profile = self._find_credit_bureau_profile(customer, db)
        if not bureau_profile:
            return evaluation

        history_result = (bureau_profile.get("preliminary_history_result") or "").upper()
        if history_result == "OBSERVADO":
            evaluation = {
                "result": "OBSERVADO",
                "reason": (
                    "El historial crediticio simulado registra riesgo "
                    f"{bureau_profile.get('risk_level')}, score "
                    f"{bureau_profile.get('credit_score')}, deuda pendiente "
                    f"{bureau_profile.get('total_outstanding_debt')}, mora maxima "
                    f"{bureau_profile.get('max_days_past_due')} dias y "
                    f"{bureau_profile.get('missed_payments')} pagos incumplidos."
                ),
                "credit_bureau": bureau_profile,
            }

        return evaluation

    def _find_credit_bureau_profile(self, customer, db):
        if customer is None or db is None:
            return None

        try:
            return CreditBureauProfileService(db).find_profile(customer.phone_number)
        except CreditBureauUnavailable:
            return None
