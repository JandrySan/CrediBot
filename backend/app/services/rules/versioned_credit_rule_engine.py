from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, ClassVar

MONEY = Decimal("0.01")
RATIO = Decimal("0.0001")


@dataclass(frozen=True)
class CreditEvaluationInput:
    amount: Decimal
    term_months: int
    monthly_net_income: Decimal | None = None
    other_monthly_income: Decimal = Decimal("0")
    monthly_living_expenses: Decimal | None = None
    existing_monthly_debt_payments: Decimal = Decimal("0")
    age: int | None = None
    employment_status: str | None = None
    job_tenure_months: int | None = None
    business_tenure_months: int | None = None
    identity_verified: bool = False
    pep_status: str = "UNKNOWN"
    credit_score: int | None = None
    max_days_past_due: int | None = None
    recent_inquiries_6m: int | None = None


@dataclass(frozen=True)
class RuleResult:
    code: str
    outcome: str
    passed: bool
    explanation: str
    observed_value: int | float | str | bool | None = None
    expected_value: int | float | str | bool | None = None


@dataclass(frozen=True)
class CreditEvaluationResult:
    result: str
    product_code: str
    policy_code: str
    is_final_decision: bool
    estimated_installment: Decimal
    verified_monthly_income: Decimal | None
    monthly_living_expenses: Decimal | None
    existing_monthly_debt_payments: Decimal
    disposable_income: Decimal | None
    current_dti: Decimal | None
    projected_dti: Decimal | None
    reason_codes: list[str]
    missing_requirements: list[str]
    rule_results: list[RuleResult]

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        for key in (
            "estimated_installment",
            "verified_monthly_income",
            "monthly_living_expenses",
            "existing_monthly_debt_payments",
            "disposable_income",
            "current_dti",
            "projected_dti",
        ):
            value[key] = _number(value[key])
        return value


class VersionedCreditRuleEngine:
    """Evalua una politica almacenada sin delegar decisiones al modelo de IA."""

    OUTCOME_PRIORITY: ClassVar[dict[str, int]] = {
        "PREQUALIFIED": 0,
        "NEEDS_INFORMATION": 1,
        "MANUAL_REVIEW": 2,
        "NOT_PREQUALIFIED": 3,
        "ERROR": 4,
    }

    def evaluate(self, product, policy, rules: list, data: CreditEvaluationInput):
        installment = self.calculate_monthly_installment(
            data.amount,
            data.term_months,
            Decimal(product.effective_annual_rate),
        )
        total_income = self._total_income(data)
        current_dti = self._ratio(data.existing_monthly_debt_payments, total_income)
        projected_dti = self._ratio(
            data.existing_monthly_debt_payments + installment,
            total_income,
        )
        disposable_income = (
            None
            if total_income is None or data.monthly_living_expenses is None
            else (
                total_income
                - data.monthly_living_expenses
                - data.existing_monthly_debt_payments
                - installment
            ).quantize(MONEY, rounding=ROUND_HALF_UP)
        )

        context = {
            "installment": installment,
            "total_income": total_income,
            "current_dti": current_dti,
            "projected_dti": projected_dti,
            "disposable_income": disposable_income,
        }
        rule_results = [self._evaluate_rule(rule, product, data, context) for rule in rules]
        failures = [result for result in rule_results if not result.passed]
        result = max(
            (failure.outcome for failure in failures),
            key=lambda outcome: self.OUTCOME_PRIORITY.get(outcome, 4),
            default="PREQUALIFIED",
        )
        reason_codes = list(dict.fromkeys(failure.code for failure in failures))
        missing_requirements = list(
            dict.fromkeys(
                failure.code for failure in failures if failure.outcome == "NEEDS_INFORMATION"
            )
        )

        return CreditEvaluationResult(
            result=result,
            product_code=product.code,
            policy_code=policy.code,
            is_final_decision=False,
            estimated_installment=installment,
            verified_monthly_income=total_income,
            monthly_living_expenses=data.monthly_living_expenses,
            existing_monthly_debt_payments=data.existing_monthly_debt_payments,
            disposable_income=disposable_income,
            current_dti=current_dti,
            projected_dti=projected_dti,
            reason_codes=reason_codes,
            missing_requirements=missing_requirements,
            rule_results=rule_results,
        )

    @staticmethod
    def calculate_monthly_installment(
        amount: Decimal,
        term_months: int,
        effective_annual_rate: Decimal,
    ) -> Decimal:
        if amount <= 0 or term_months <= 0:
            return Decimal("0")
        if effective_annual_rate <= 0:
            return (amount / term_months).quantize(MONEY, rounding=ROUND_HALF_UP)

        annual_factor = Decimal("1") + (effective_annual_rate / Decimal("100"))
        monthly_rate = annual_factor ** (Decimal("1") / Decimal("12")) - Decimal("1")
        factor = (Decimal("1") + monthly_rate) ** term_months
        installment = amount * monthly_rate * factor / (factor - Decimal("1"))
        return installment.quantize(MONEY, rounding=ROUND_HALF_UP)

    def _evaluate_rule(self, rule, product, data, context: dict) -> RuleResult:
        handler = getattr(self, f"_rule_{rule.code.lower()}", None)
        if handler is None:
            return RuleResult(
                code=f"UNSUPPORTED_{rule.code}",
                outcome="MANUAL_REVIEW",
                passed=False,
                explanation="La regla no tiene un evaluador determinista registrado.",
            )
        return handler(rule, product, data, context)

    def _rule_amount_in_range(self, rule, product, data, _context) -> RuleResult:
        minimum = Decimal(product.min_amount)
        maximum = Decimal(product.max_amount)
        passed = minimum <= data.amount <= maximum
        return self._result(rule, passed, data.amount, f"{minimum}-{maximum}")

    def _rule_term_in_range(self, rule, product, data, _context) -> RuleResult:
        passed = product.min_term_months <= data.term_months <= product.max_term_months
        return self._result(
            rule,
            passed,
            data.term_months,
            f"{product.min_term_months}-{product.max_term_months}",
        )

    def _rule_minimum_age(self, rule, _product, data, _context) -> RuleResult:
        minimum = int(rule.parameters["minimum_age"])
        if data.age is None:
            return self._missing(rule, "AGE_REQUIRED")
        return self._result(rule, data.age >= minimum, data.age, minimum)

    def _rule_maximum_age_at_maturity(self, rule, _product, data, _context) -> RuleResult:
        maximum = int(rule.parameters["maximum_age"])
        if data.age is None:
            return self._missing(rule, "AGE_REQUIRED")
        age_at_maturity = data.age + (data.term_months / 12)
        return self._result(rule, age_at_maturity <= maximum, round(age_at_maturity, 2), maximum)

    def _rule_identity_verified(self, rule, _product, data, _context) -> RuleResult:
        return self._result(rule, data.identity_verified, data.identity_verified, True)

    def _rule_pep_review(self, rule, _product, data, _context) -> RuleResult:
        normalized = (data.pep_status or "UNKNOWN").upper()
        if normalized == "UNKNOWN":
            return self._missing(rule, "PEP_STATUS_REQUIRED")
        return self._result(rule, normalized == "NOT_PEP", normalized, "NOT_PEP")

    def _rule_minimum_monthly_income(self, rule, _product, data, context) -> RuleResult:
        minimum = Decimal(str(rule.parameters["minimum"]))
        income = context["total_income"]
        if income is None:
            return self._missing(rule, "INCOME_REQUIRED")
        return self._result(rule, income >= minimum, income, minimum)

    def _rule_expenses_declared(self, rule, _product, data, _context) -> RuleResult:
        if data.monthly_living_expenses is None:
            return self._missing(rule, "EXPENSES_REQUIRED")
        return self._result(
            rule, data.monthly_living_expenses >= 0, data.monthly_living_expenses, 0
        )

    def _rule_maximum_projected_dti(self, rule, _product, _data, context) -> RuleResult:
        maximum = Decimal(str(rule.parameters["maximum"]))
        projected_dti = context["projected_dti"]
        if projected_dti is None:
            return self._missing(rule, "INCOME_REQUIRED")
        return self._result(rule, projected_dti <= maximum, projected_dti, maximum)

    def _rule_minimum_disposable_after_payment(self, rule, _product, _data, context):
        minimum = Decimal(str(rule.parameters["minimum"]))
        disposable = context["disposable_income"]
        if disposable is None:
            return self._missing(rule, "EXPENSES_REQUIRED")
        return self._result(rule, disposable >= minimum, disposable, minimum)

    def _rule_minimum_employment_tenure(self, rule, _product, data, _context):
        if (data.employment_status or "").upper() != "EMPLOYED":
            return self._result(rule, True, data.employment_status, "EMPLOYED")
        if data.job_tenure_months is None:
            return self._missing(rule, "JOB_TENURE_REQUIRED")
        minimum = int(rule.parameters["months"])
        return self._result(
            rule, data.job_tenure_months >= minimum, data.job_tenure_months, minimum
        )

    def _rule_minimum_business_tenure(self, rule, _product, data, _context):
        if (data.employment_status or "").upper() != "SELF_EMPLOYED":
            return self._result(rule, True, data.employment_status, "SELF_EMPLOYED")
        if data.business_tenure_months is None:
            return self._missing(rule, "BUSINESS_TENURE_REQUIRED")
        minimum = int(rule.parameters["months"])
        return self._result(
            rule,
            data.business_tenure_months >= minimum,
            data.business_tenure_months,
            minimum,
        )

    def _rule_minimum_credit_score(self, rule, _product, data, _context):
        if data.credit_score is None:
            return self._missing(rule, "CREDIT_HISTORY_REQUIRED")
        minimum = int(rule.parameters["minimum"])
        return self._result(rule, data.credit_score >= minimum, data.credit_score, minimum)

    def _rule_no_active_severe_delinquency(self, rule, _product, data, _context):
        if data.max_days_past_due is None:
            return self._missing(rule, "CREDIT_HISTORY_REQUIRED")
        maximum = int(rule.parameters["maximum_days_past_due"])
        return self._result(
            rule, data.max_days_past_due <= maximum, data.max_days_past_due, maximum
        )

    def _rule_maximum_recent_inquiries(self, rule, _product, data, _context):
        if data.recent_inquiries_6m is None:
            return self._missing(rule, "CREDIT_HISTORY_REQUIRED")
        maximum = int(rule.parameters["maximum_6m"])
        return self._result(
            rule, data.recent_inquiries_6m <= maximum, data.recent_inquiries_6m, maximum
        )

    @staticmethod
    def _total_income(data: CreditEvaluationInput) -> Decimal | None:
        if data.monthly_net_income is None:
            return None
        return (data.monthly_net_income + data.other_monthly_income).quantize(
            MONEY, rounding=ROUND_HALF_UP
        )

    @staticmethod
    def _ratio(numerator: Decimal, denominator: Decimal | None) -> Decimal | None:
        if denominator is None or denominator <= 0:
            return None
        return (numerator / denominator).quantize(RATIO, rounding=ROUND_HALF_UP)

    @staticmethod
    def _result(rule, passed: bool, observed, expected) -> RuleResult:
        return RuleResult(
            code=rule.code,
            outcome=rule.outcome_on_failure,
            passed=passed,
            explanation=rule.explanation,
            observed_value=_number(observed),
            expected_value=_number(expected),
        )

    @staticmethod
    def _missing(rule, code: str) -> RuleResult:
        return RuleResult(
            code=code,
            outcome="NEEDS_INFORMATION",
            passed=False,
            explanation=rule.explanation,
        )


def _number(value):
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, Decimal):
        if value == value.to_integral_value():
            return int(value)
        return float(value)
    return value
