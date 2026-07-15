from __future__ import annotations

from dataclasses import replace
from decimal import Decimal

from app.repositories.credit_catalog_repository import CreditCatalogRepository
from app.repositories.credit_decision_repository import CreditDecisionRepository
from app.services.rules.versioned_credit_rule_engine import (
    CreditEvaluationInput,
    VersionedCreditRuleEngine,
)


class CreditPrequalificationService:
    def __init__(self, db, slot_service):
        self.db = db
        self.slots = slot_service
        self.catalog = CreditCatalogRepository(db)
        self.decisions = CreditDecisionRepository(db)
        self.engine = VersionedCreditRuleEngine()

    def evaluate(self, context, application, bureau_profile: dict | None = None) -> dict:
        product = self.catalog.resolve_product(self.slots.value(context, "product_code"))
        policy = self.catalog.get_active_policy()
        if product is None or policy is None:
            return {
                "result": "ERROR",
                "reason": "No existe un producto o una politica vigente para evaluar.",
            }

        rules = self.catalog.list_active_rules(policy.id, product.id)
        employment = self.slots.value(context, "employment_status")
        tenure = self._integer(self.slots.value(context, "employment_tenure"))
        evaluation_input = CreditEvaluationInput(
            amount=self._decimal(self.slots.value(context, "amount")),
            term_months=self._integer(self.slots.value(context, "term_months")) or 0,
            monthly_net_income=self._optional_decimal(self.slots.value(context, "monthly_income")),
            other_monthly_income=self._decimal(
                self.slots.value(context, "other_monthly_income", 0)
            ),
            monthly_living_expenses=self._optional_decimal(
                self.slots.value(context, "monthly_expenses")
            ),
            existing_monthly_debt_payments=self._decimal(
                self.slots.value(context, "existing_debt_payments", 0)
            ),
            age=self._integer(self.slots.value(context, "age")),
            employment_status=employment,
            job_tenure_months=tenure if employment == "EMPLOYED" else None,
            business_tenure_months=tenure if employment == "SELF_EMPLOYED" else None,
            identity_verified=bool(self.slots.value(context, "identity_verified", False)),
            pep_status=self.slots.value(context, "pep_status", "UNKNOWN"),
            credit_score=self._integer(self.slots.value(context, "credit_score")),
            max_days_past_due=self._integer(self.slots.value(context, "max_days_past_due")),
            recent_inquiries_6m=self._integer(self.slots.value(context, "recent_inquiries_6m")),
        )
        evaluation = self.engine.evaluate(product, policy, rules, evaluation_input)
        if self.slots.status(context, "bureau_consent") == "DECLINED":
            evaluation = replace(evaluation, result="SIMULATION_ONLY")
        snapshot = self.slots.snapshot(context)
        snapshot.update(
            {
                "amount": evaluation_input.amount,
                "term_months": evaluation_input.term_months,
                "bureau_profile_found": bureau_profile is not None,
            }
        )
        self.decisions.save_from_evaluation(
            application_id=application.id,
            product_id=product.id,
            policy_version_id=policy.id,
            evaluation=evaluation,
            credit_score=evaluation_input.credit_score,
            risk_level=(bureau_profile or {}).get("risk_level"),
            input_snapshot=self._json_safe(snapshot),
        )
        application.product_id = product.id
        application.credit_type = product.segment
        application.status = evaluation.result
        application.result = evaluation.result
        application.reason = self._reason(evaluation)
        self.db.flush()

        result = evaluation.to_dict()
        result["reason"] = application.reason
        result["product_name"] = product.name
        result["is_demo"] = product.is_demo
        if evaluation.result == "SIMULATION_ONLY":
            result["reason"] = (
                "Se calculo la capacidad declarada, pero no se consulto ni verifico el "
                "historial porque no autorizaste la central simulada."
            )
            application.reason = result["reason"]
        return result

    @staticmethod
    def _reason(evaluation) -> str:
        failures = [item.explanation for item in evaluation.rule_results if not item.passed]
        unique = list(dict.fromkeys(failures))
        if not unique:
            return "Cumple las reglas demostrativas de la politica vigente."
        return " ".join(unique)

    @staticmethod
    def _decimal(value) -> Decimal:
        return Decimal(str(value or 0))

    @staticmethod
    def _optional_decimal(value) -> Decimal | None:
        return None if value is None else Decimal(str(value))

    @staticmethod
    def _integer(value) -> int | None:
        return None if value is None else int(value)

    @classmethod
    def _json_safe(cls, value):
        if isinstance(value, Decimal):
            return str(value)
        if isinstance(value, dict):
            return {key: cls._json_safe(item) for key, item in value.items()}
        if isinstance(value, list):
            return [cls._json_safe(item) for item in value]
        return value
