from decimal import Decimal
from types import SimpleNamespace

from app.services.rules.versioned_credit_rule_engine import (
    CreditEvaluationInput,
    VersionedCreditRuleEngine,
)


def _product():
    return SimpleNamespace(
        code="CONSUMO_PERSONAL_DEMO",
        min_amount=Decimal("500"),
        max_amount=Decimal("30000"),
        min_term_months=6,
        max_term_months=60,
        effective_annual_rate=Decimal("15.50"),
    )


def _policy():
    return SimpleNamespace(code="DEMO_EC_TEST")


def _rule(code, parameters, outcome="NOT_PREQUALIFIED"):
    return SimpleNamespace(
        code=code,
        parameters=parameters,
        outcome_on_failure=outcome,
        explanation=f"Explicacion de {code}",
    )


def test_complete_profile_is_prequalified_with_auditable_calculations():
    engine = VersionedCreditRuleEngine()
    result = engine.evaluate(
        product=_product(),
        policy=_policy(),
        rules=[
            _rule("AMOUNT_IN_RANGE", {"use_product_range": True}),
            _rule("TERM_IN_RANGE", {"use_product_range": True}),
            _rule("MINIMUM_MONTHLY_INCOME", {"minimum": 600}),
            _rule("EXPENSES_DECLARED", {"required": True}),
            _rule("MAXIMUM_PROJECTED_DTI", {"maximum": 0.40}),
            _rule("MINIMUM_DISPOSABLE_AFTER_PAYMENT", {"minimum": 100}),
        ],
        data=CreditEvaluationInput(
            amount=Decimal("2000"),
            term_months=24,
            monthly_net_income=Decimal("1800"),
            monthly_living_expenses=Decimal("600"),
            existing_monthly_debt_payments=Decimal("150"),
        ),
    )

    assert result.result == "PREQUALIFIED"
    assert result.estimated_installment == Decimal("96.50")
    assert result.projected_dti == Decimal("0.1369")
    assert result.disposable_income == Decimal("953.50")
    assert result.reason_codes == []
    assert result.is_final_decision is False


def test_missing_expenses_requests_information_instead_of_assuming_zero():
    result = VersionedCreditRuleEngine().evaluate(
        product=_product(),
        policy=_policy(),
        rules=[
            _rule("EXPENSES_DECLARED", {"required": True}),
            _rule("MINIMUM_DISPOSABLE_AFTER_PAYMENT", {"minimum": 100}),
        ],
        data=CreditEvaluationInput(
            amount=Decimal("2000"),
            term_months=24,
            monthly_net_income=Decimal("1800"),
        ),
    )

    assert result.result == "NEEDS_INFORMATION"
    assert result.missing_requirements == ["EXPENSES_REQUIRED"]
    assert result.monthly_living_expenses is None


def test_known_blocking_failure_takes_priority_over_missing_data():
    result = VersionedCreditRuleEngine().evaluate(
        product=_product(),
        policy=_policy(),
        rules=[
            _rule("AMOUNT_IN_RANGE", {"use_product_range": True}),
            _rule("EXPENSES_DECLARED", {"required": True}),
        ],
        data=CreditEvaluationInput(
            amount=Decimal("50000"),
            term_months=24,
            monthly_net_income=Decimal("1800"),
        ),
    )

    assert result.result == "NOT_PREQUALIFIED"
    assert result.reason_codes == ["AMOUNT_IN_RANGE", "EXPENSES_REQUIRED"]


def test_unknown_policy_rule_fails_safe_to_manual_review():
    result = VersionedCreditRuleEngine().evaluate(
        product=_product(),
        policy=_policy(),
        rules=[_rule("NEW_UNSUPPORTED_RULE", {})],
        data=CreditEvaluationInput(
            amount=Decimal("2000"),
            term_months=24,
            monthly_net_income=Decimal("1800"),
            monthly_living_expenses=Decimal("500"),
        ),
    )

    assert result.result == "MANUAL_REVIEW"
    assert result.reason_codes == ["UNSUPPORTED_NEW_UNSUPPORTED_RULE"]
