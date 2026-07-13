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
                credit_score,
                risk_level,
                total_outstanding_debt,
                max_days_past_due,
                missed_payments,
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
            "credit_score": self._to_int(row["credit_score"]),
            "risk_level": row["risk_level"],
            "total_outstanding_debt": self._to_number(row["total_outstanding_debt"]),
            "max_days_past_due": self._to_int(row["max_days_past_due"]),
            "missed_payments": self._to_int(row["missed_payments"]),
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
