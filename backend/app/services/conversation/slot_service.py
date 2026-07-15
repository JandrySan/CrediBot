from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any, ClassVar


class ConversationSlotService:
    """Mantiene datos conversacionales corregibles sin imponer el orden del mensaje."""

    SLOT_ORDER: ClassVar[tuple[str, ...]] = (
        "privacy_consent",
        "product_code",
        "national_id",
        "bureau_consent",
        "full_name",
        "age",
        "employment_status",
        "employment_tenure",
        "amount",
        "term_months",
        "monthly_income",
        "monthly_expenses",
        "existing_debt_payments",
        "pep_status",
    )
    ENTITY_FIELDS: ClassVar[frozenset[str]] = frozenset(
        {
            "product_code",
            "national_id",
            "full_name",
            "age",
            "employment_status",
            "employment_tenure",
            "amount",
            "term_months",
            "monthly_income",
            "monthly_expenses",
            "existing_debt_payments",
            "pep_status",
            "purpose",
            "other_monthly_income",
        }
    )

    def apply_entities(
        self,
        context,
        entities: dict,
        source: str = "USER_MESSAGE",
        confidence: float = 0.85,
    ) -> list[str]:
        changed: list[str] = []
        for field in self.ENTITY_FIELDS:
            value = entities.get(field)
            if value is None or value == "":
                continue
            if self.set_slot(
                context,
                field,
                value,
                status="CONFIRMED",
                source=source,
                confidence=confidence,
            ):
                changed.append(field)
        return changed

    def set_slot(
        self,
        context,
        field: str,
        value: Any,
        status: str,
        source: str,
        confidence: float = 1.0,
    ) -> bool:
        serialized = self._serialize(value)
        slots = dict(context.slots or {})
        previous = slots.get(field)
        if previous and previous.get("value") == serialized and previous.get("status") == status:
            return False

        history = list(previous.get("history", [])) if previous else []
        if previous:
            history.append(
                {
                    "value": previous.get("value"),
                    "status": previous.get("status"),
                    "source": previous.get("source"),
                    "updated_at": previous.get("updated_at"),
                }
            )
        slots[field] = {
            "value": serialized,
            "status": status,
            "source": source,
            "confidence": round(float(confidence), 4),
            "updated_at": datetime.now(UTC).isoformat(timespec="seconds"),
            "history": history[-5:],
        }
        context.slots = slots
        context.revision = (context.revision or 0) + 1
        return True

    @staticmethod
    def value(context, field: str, default=None):
        slot = (context.slots or {}).get(field) or {}
        return slot.get("value", default)

    @staticmethod
    def status(context, field: str) -> str:
        slot = (context.slots or {}).get(field) or {}
        return slot.get("status", "UNKNOWN")

    def next_required_field(self, context) -> str | None:
        for field in self.SLOT_ORDER:
            if self._is_required(context, field) and not self._is_available(context, field):
                return field
        return None

    def snapshot(self, context) -> dict[str, Any]:
        return {
            field: slot.get("value")
            for field, slot in (context.slots or {}).items()
            if slot.get("status") not in {"UNKNOWN", "REVOKED"}
        }

    def _is_available(self, context, field: str) -> bool:
        return self.status(context, field) in {
            "CONFIRMED",
            "VERIFIED",
            "GRANTED",
            "DECLINED",
        }

    def _is_required(self, context, field: str) -> bool:
        if field == "employment_tenure":
            return self.value(context, "employment_status") in {"EMPLOYED", "SELF_EMPLOYED"}
        if field == "bureau_consent":
            return bool(self.value(context, "national_id"))
        return True

    @staticmethod
    def _serialize(value):
        if isinstance(value, Decimal):
            return str(value)
        if isinstance(value, (date, datetime)):
            return value.isoformat()
        return value
