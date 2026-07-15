import re
import unicodedata
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
        if data.get("national_id") and not getattr(customer, "national_id", None):
            normalized_national_id = self._normalize_national_id(data["national_id"])
            if len(normalized_national_id) == 10:
                customer.national_id = normalized_national_id
                profile = self._find_credit_bureau_profile(customer, db)
                if profile and profile.get("full_name") and not customer.full_name:
                    customer.full_name = profile["full_name"]

        full_name = (data.get("full_name") or "").strip()
        if full_name and not customer.full_name and self.is_valid_person_name(full_name):
            customer.full_name = full_name

        if data.get("amount") and application.amount is None:
            application.amount = Decimal(str(data["amount"]))

        if data.get("term_months") and application.term_months is None:
            application.term_months = int(data["term_months"])

        if data.get("monthly_income") and application.monthly_income is None:
            application.monthly_income = Decimal(str(data["monthly_income"]))

        db.flush()

    @classmethod
    def is_valid_person_name(cls, value: str) -> bool:
        normalized = cls._normalize_text(value)
        if not normalized:
            return False

        blocked_tokens = {
            "audio",
            "texto",
            "responde",
            "respondeme",
            "responder",
            "respondiendo",
            "contestame",
            "mandame",
            "enviame",
            "credito",
            "creditos",
            "prestamo",
            "prestamos",
            "monto",
            "dolares",
            "plazo",
            "ingreso",
            "ingresos",
            "asesor",
            "hola",
            "buenas",
        }
        words = normalized.split()

        if any(word in blocked_tokens for word in words):
            return False

        if len(words) < 2:
            return False

        return bool(re.fullmatch(r"[a-zñ]+(?:\s+[a-zñ]+){1,5}", normalized))

    @staticmethod
    def _normalize_text(value: str) -> str:
        normalized = (value or "").strip().lower()
        normalized = "".join(
            char
            for char in unicodedata.normalize("NFD", normalized)
            if unicodedata.category(char) != "Mn"
        )
        normalized = re.sub(r"[^a-zñ\s]", " ", normalized)
        return re.sub(r"\s+", " ", normalized).strip()

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
            monthly_income=Decimal(application.monthly_income),
        )

        bureau_profile = self._find_credit_bureau_profile(customer, db)
        if not bureau_profile:
            return evaluation

        history_result = (bureau_profile.get("preliminary_history_result") or "").upper()
        if history_result == "OBSERVADO":
            reason_parts = [
                f"estado central {bureau_profile.get('central_risk_status')}",
                f"riesgo {bureau_profile.get('risk_level')}",
                f"score {bureau_profile.get('credit_score')}",
                f"deuda pendiente {bureau_profile.get('total_outstanding_debt')}",
                f"mora maxima {bureau_profile.get('max_days_past_due')} dias",
                f"{bureau_profile.get('missed_payments')} pagos incumplidos",
            ]
            if bureau_profile.get("central_risk_reason"):
                reason_parts.append(str(bureau_profile.get("central_risk_reason")))

            evaluation = {
                "result": "OBSERVADO",
                "reason": (f"La central de riesgo simulada registra {', '.join(reason_parts)}."),
                "credit_bureau": bureau_profile,
            }

        return evaluation

    def _find_credit_bureau_profile(self, customer, db):
        if customer is None or db is None:
            return None

        try:
            return CreditBureauProfileService(db).find_first_available(
                getattr(customer, "national_id", None),
                customer.phone_number,
            )
        except CreditBureauUnavailable:
            return None

    def _normalize_national_id(self, value) -> str:
        return "".join(ch for ch in str(value or "") if ch.isdigit())[:10]
