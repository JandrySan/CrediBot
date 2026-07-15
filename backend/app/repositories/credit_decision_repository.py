from sqlalchemy.orm import Session

from app.models.credit_decision import CreditDecision


class CreditDecisionRepository:
    def __init__(self, db: Session):
        self.db = db

    def save_from_evaluation(
        self,
        application_id: int,
        product_id: int,
        policy_version_id: int,
        evaluation,
        credit_score: int | None,
        risk_level: str | None,
        input_snapshot: dict,
    ) -> CreditDecision:
        decision = CreditDecision(
            application_id=application_id,
            product_id=product_id,
            policy_version_id=policy_version_id,
            result=evaluation.result,
            is_final_decision=False,
            requested_amount=input_snapshot["amount"],
            proposed_term_months=input_snapshot["term_months"],
            estimated_installment=evaluation.estimated_installment,
            verified_monthly_income=evaluation.verified_monthly_income,
            monthly_living_expenses=evaluation.monthly_living_expenses,
            existing_monthly_debt_payments=evaluation.existing_monthly_debt_payments,
            disposable_income=evaluation.disposable_income,
            current_dti=evaluation.current_dti,
            projected_dti=evaluation.projected_dti,
            credit_score=credit_score,
            risk_level=risk_level,
            reason_codes=evaluation.reason_codes,
            missing_requirements=evaluation.missing_requirements,
            input_snapshot=input_snapshot,
        )
        self.db.add(decision)
        self.db.flush()
        return decision
