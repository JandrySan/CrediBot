import re
from decimal import Decimal, InvalidOperation

from app.services.conversation.conversation_state_service import ConversationStateService
from app.services.conversation.credit_application_service import CreditApplicationService
from app.state_machine.states import ConversationState


class ConversationInputExtractor:
    """Completa de forma determinista los datos que la IA no pudo extraer."""

    def __init__(
        self,
        state_service: ConversationStateService,
        credit_service: CreditApplicationService,
    ):
        self.state_service = state_service
        self.credit_service = credit_service

    def enrich(
        self,
        conversation,
        customer,
        application,
        text: str,
        ai_data: dict,
    ) -> dict:
        enriched = dict(ai_data or {})
        expected_field = self.expected_field(conversation, customer, application)

        if not expected_field or enriched.get(expected_field):
            return enriched

        extractor = {
            "national_id": self.extract_national_id,
            "full_name": self.extract_name,
            "term_months": self.extract_term_months,
            "amount": self.extract_decimal,
            "monthly_income": self.extract_decimal,
        }.get(expected_field)

        if extractor is None:
            return enriched

        value = extractor(text)
        if value is not None:
            enriched[expected_field] = (
                str(value) if expected_field in {"amount", "monthly_income"} else value
            )

        return enriched

    def expected_field(self, conversation, customer, application) -> str | None:
        by_state = {
            ConversationState.ASK_NATIONAL_ID.value: "national_id",
            ConversationState.ASK_NAME.value: "full_name",
            ConversationState.ASK_AMOUNT.value: "amount",
            ConversationState.ASK_TERM.value: "term_months",
            ConversationState.ASK_INCOME.value: "monthly_income",
        }
        return by_state.get(
            conversation.current_state
        ) or self.state_service.get_next_required_field(customer, application)

    @staticmethod
    def extract_national_id(text: str) -> str | None:
        match = re.search(r"\b\d{10}\b", (text or "").strip())
        return match.group(0) if match else None

    def extract_name(self, text: str) -> str | None:
        value = (text or "").strip()
        if not value or re.search(r"\d", value):
            return None

        cleaned = re.sub(r"[^A-Za-zÁÉÍÓÚáéíóúÑñÜü\s]", " ", value)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        if len(cleaned) < 2 or cleaned.lower() in {
            "hola",
            "buenas",
            "gracias",
            "ok",
            "credito",
        }:
            return None

        if not self.credit_service.is_valid_person_name(cleaned):
            return None

        return cleaned[:120]

    @staticmethod
    def extract_decimal(text: str) -> Decimal | None:
        match = re.search(r"\d[\d\.,]*", (text or "").strip())
        if not match:
            return None

        normalized = match.group(0).replace(",", "").replace(" ", "")
        try:
            return Decimal(normalized)
        except InvalidOperation:
            return None

    @staticmethod
    def extract_term_months(text: str) -> int | None:
        value = (text or "").lower().strip()
        match = re.search(r"\d+", value)
        if not match:
            return None

        number = int(match.group(0))
        if number <= 0:
            return None

        return (
            number * 12
            if any(token in value for token in ("ano", "anos", "year", "years"))
            else number
        )

    def clear_invalid_customer_name(self, customer) -> bool:
        full_name = (getattr(customer, "full_name", "") or "").strip()
        if not full_name or self.credit_service.is_valid_person_name(full_name):
            return False

        customer.full_name = None
        return True
