from decimal import Decimal
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session


class CreditBureauUnavailable(Exception):
    pass


class CreditBureauProfileService:
    def __init__(self, db: Session):
        self.db = db

    def find_profile(self, identifier: str) -> dict[str, Any] | None:
        normalized = self._normalize_identifier(identifier)
        if not normalized:
            return None

        query = text(
            """
            SELECT
                national_id,
                phone_number,
                full_name,
                age,
                province,
                city,
                employment_status,
                occupation,
                reported_monthly_income,
                central_risk_status,
                central_risk_reason,
                credit_score,
                risk_level,
                total_accounts,
                active_accounts,
                problematic_accounts,
                total_outstanding_debt,
                total_monthly_debt_payment,
                debt_to_income_ratio,
                max_days_past_due,
                missed_payments,
                late_payments,
                written_off_accounts,
                judicial_collection_events,
                restructured_accounts,
                recent_inquiries_6m,
                recommended_max_installment,
                preliminary_history_result
            FROM credit_bureau.find_profile(:identifier)
            """
        )

        try:
            row = self.db.execute(query, {"identifier": normalized}).mappings().first()
        except SQLAlchemyError as exc:
            raise CreditBureauUnavailable(str(exc)) from exc

        if row is None:
            return None

        return {
            "national_id": row.get("national_id"),
            "phone_number": row.get("phone_number"),
            "full_name": row.get("full_name"),
            "age": self._to_int(row.get("age")),
            "province": row.get("province"),
            "city": row.get("city"),
            "employment_status": row.get("employment_status"),
            "occupation": row.get("occupation"),
            "reported_monthly_income": self._to_number(row.get("reported_monthly_income")),
            "central_risk_status": row.get("central_risk_status"),
            "central_risk_reason": row.get("central_risk_reason"),
            "credit_score": self._to_int(row["credit_score"]),
            "risk_level": row["risk_level"],
            "total_accounts": self._to_int(row.get("total_accounts")),
            "active_accounts": self._to_int(row.get("active_accounts")),
            "problematic_accounts": self._to_int(row.get("problematic_accounts")),
            "total_outstanding_debt": self._to_number(row["total_outstanding_debt"]),
            "total_monthly_debt_payment": self._to_number(row.get("total_monthly_debt_payment")),
            "debt_to_income_ratio": self._to_number(row.get("debt_to_income_ratio")),
            "max_days_past_due": self._to_int(row["max_days_past_due"]),
            "missed_payments": self._to_int(row["missed_payments"]),
            "late_payments": self._to_int(row.get("late_payments")),
            "written_off_accounts": self._to_int(row.get("written_off_accounts")),
            "judicial_collection_events": self._to_int(row.get("judicial_collection_events")),
            "restructured_accounts": self._to_int(row.get("restructured_accounts")),
            "recent_inquiries_6m": self._to_int(row.get("recent_inquiries_6m")),
            "recommended_max_installment": self._to_number(row.get("recommended_max_installment")),
            "preliminary_history_result": row["preliminary_history_result"],
        }

    def find_first_available(self, *identifiers: str | None) -> dict[str, Any] | None:
        for identifier in identifiers:
            profile = self.find_profile(identifier or "")
            if profile:
                return profile

        return None

    def _normalize_identifier(self, identifier: str) -> str:
        value = (identifier or "").strip()
        if value.lower().startswith("whatsapp:"):
            value = value.split(":", 1)[1].strip()

        return value

    def _to_int(self, value) -> int | None:
        if value is None:
            return None

        return int(value)

    def _to_number(self, value):
        if value is None:
            return None

        if isinstance(value, Decimal):
            if value == value.to_integral_value():
                return int(value)

            return float(value)

        return value
