from decimal import Decimal
from types import SimpleNamespace

from app.services.conversation.credit_application_service import CreditApplicationService


class _ProfileService:
    def __init__(self, db):
        self.db = db

    def find_profile(self, identifier):
        return {
            "credit_score": 485,
            "risk_level": "HIGH",
            "total_outstanding_debt": 2100,
            "max_days_past_due": 90,
            "missed_payments": 3,
            "preliminary_history_result": "OBSERVADO",
        }


def test_evaluation_uses_observed_credit_bureau_profile(monkeypatch):
    import app.services.conversation.credit_application_service as service_module

    monkeypatch.setattr(service_module, "CreditBureauProfileService", _ProfileService)

    service = CreditApplicationService()
    customer = SimpleNamespace(phone_number="+593990000003")
    application = SimpleNamespace(
        amount=Decimal("1000"),
        term_months=12,
        monthly_income=Decimal("900"),
        result=None,
    )

    evaluation = service.evaluate_if_complete(application, customer=customer, db=object())

    assert evaluation["result"] == "OBSERVADO"
    assert evaluation["credit_bureau"] == {
        "credit_score": 485,
        "risk_level": "HIGH",
        "total_outstanding_debt": 2100,
        "max_days_past_due": 90,
        "missed_payments": 3,
        "preliminary_history_result": "OBSERVADO",
    }
