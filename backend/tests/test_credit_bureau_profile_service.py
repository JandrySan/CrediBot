from decimal import Decimal

from app.services.credit_bureau.profile_service import CreditBureauProfileService


class _FakeResult:
    def __init__(self, row):
        self.row = row

    def mappings(self):
        return self

    def first(self):
        return self.row


class _FakeDb:
    def __init__(self, row):
        self.row = row
        self.params = None

    def execute(self, query, params):
        self.params = params
        return _FakeResult(self.row)


def test_find_profile_returns_credibot_contract():
    db = _FakeDb({
        "credit_score": 485,
        "risk_level": "HIGH",
        "total_outstanding_debt": Decimal("2100.00"),
        "max_days_past_due": 90,
        "missed_payments": 3,
        "preliminary_history_result": "OBSERVADO",
    })

    profile = CreditBureauProfileService(db).find_profile("9990000003")

    assert db.params == {"identifier": "9990000003"}
    assert profile == {
        "credit_score": 485,
        "risk_level": "HIGH",
        "total_outstanding_debt": 2100,
        "max_days_past_due": 90,
        "missed_payments": 3,
        "preliminary_history_result": "OBSERVADO",
    }


def test_find_profile_normalizes_whatsapp_prefix():
    db = _FakeDb(None)

    profile = CreditBureauProfileService(db).find_profile("whatsapp:+593990000003")

    assert profile is None
    assert db.params == {"identifier": "+593990000003"}
