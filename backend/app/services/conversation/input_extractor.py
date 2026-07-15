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
        deterministic = self.extract_additional(text)
        for field, value in deterministic.items():
            if enriched.get(field) is None and value is not None:
                enriched[field] = value

        expected_field = self.expected_field(conversation, customer, application)

        if not expected_field or enriched.get(expected_field) is not None:
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

    def enrich_pending_field(self, text: str, field: str | None, data: dict) -> dict:
        enriched = dict(data or {})
        self._sanitize_name_entity(text, field, enriched)
        if not field or enriched.get(field) is not None:
            return enriched
        numeric_fields = {
            "age",
            "employment_tenure",
            "amount",
            "term_months",
            "monthly_income",
            "monthly_expenses",
            "existing_debt_payments",
        }
        if field in numeric_fields and re.fullmatch(
            r"\s*[$]?\s*\d[\d\.,]*\s*(?:mes(?:es)?|a(?:n|ñ)os?|dolares?)?\s*",
            (text or "").lower(),
        ):
            for other_field in numeric_fields - {field}:
                enriched.pop(other_field, None)
        additional = self.extract_additional(text)
        if additional.get(field) is not None:
            enriched[field] = additional[field]
            return enriched
        normalized = (text or "").strip().lower()
        if field == "pep_status":
            if normalized in {"no", "no soy", "ninguna", "not pep"}:
                enriched[field] = "NOT_PEP"
            elif normalized in {"si", "sí", "soy", "soy pep"}:
                enriched[field] = "PEP"
            elif "no estoy seguro" in normalized:
                enriched[field] = "UNKNOWN"
            return enriched
        extractor = {
            "national_id": self.extract_national_id,
            "full_name": self.extract_name,
            "age": self.extract_integer,
            "employment_tenure": self.extract_term_months,
            "amount": self.extract_decimal,
            "term_months": self.extract_term_months,
            "monthly_income": self.extract_decimal,
            "monthly_expenses": self.extract_decimal,
            "existing_debt_payments": self.extract_decimal,
        }.get(field)
        if extractor:
            value = extractor(text)
            if value is not None:
                enriched[field] = str(value) if isinstance(value, Decimal) else value
        return enriched

    def extract_additional(self, text: str) -> dict:
        normalized = (text or "").lower()
        result: dict = {}
        national_id = self.extract_national_id(text)
        if national_id:
            result["national_id"] = national_id
        if any(word in normalized for word in ("microcredito", "microcrédito", "negocio")):
            result["product_code"] = "MICROCREDITO_MINORISTA_DEMO"
        elif any(word in normalized for word in ("consumo", "personal", "gastos personales")):
            result["product_code"] = "CONSUMO_PERSONAL_DEMO"

        age_match = re.search(r"(?:tengo|edad(?:\s+de)?)\s+(\d{1,2})\s+a(?:n|ñ)os", normalized)
        if age_match:
            result["age"] = int(age_match.group(1))
        if any(word in normalized for word in ("independiente", "negocio propio", "ruc")):
            result["employment_status"] = "SELF_EMPLOYED"
        elif any(word in normalized for word in ("empleado", "dependencia", "asalariado")):
            result["employment_status"] = "EMPLOYED"
        elif any(word in normalized for word in ("jubilado", "pensionista")):
            result["employment_status"] = "RETIRED"
        elif "desempleado" in normalized:
            result["employment_status"] = "UNEMPLOYED"
        elif "estudiante" in normalized:
            result["employment_status"] = "STUDENT"

        number = self.extract_decimal(text)
        if number is not None:
            if any(word in normalized for word in ("gasto", "egreso")):
                result["monthly_expenses"] = str(number)
            elif any(word in normalized for word in ("deuda", "cuotas actuales", "pago deudas")):
                result["existing_debt_payments"] = str(number)
            elif any(word in normalized for word in ("ingreso", "sueldo", "gano", "mensual")):
                result["monthly_income"] = str(number)
            elif any(word in normalized for word in ("monto", "solicito", "necesito", "credito")):
                result["amount"] = str(number)
        term = self.extract_term_months(text)
        if (
            term
            and age_match is None
            and any(word in normalized for word in ("plazo", "mes", "ano", "año"))
        ):
            if any(word in normalized for word in ("antiguedad", "trabajo", "negocio hace")):
                result["employment_tenure"] = term
            else:
                result["term_months"] = term
        if "no soy pep" in normalized:
            result["pep_status"] = "NOT_PEP"
        elif "soy pep" in normalized:
            result["pep_status"] = "PEP"
        explicit_name = self.extract_explicit_name(text)
        if explicit_name:
            result["full_name"] = explicit_name
        return result

    def _sanitize_name_entity(self, text: str, pending_field: str | None, data: dict) -> None:
        explicit_name = self.extract_explicit_name(text)
        if explicit_name:
            data["full_name"] = explicit_name
            return

        bare_name = self.extract_name(text)
        if bare_name and pending_field == "full_name" and self._looks_like_bare_name(text):
            data["full_name"] = bare_name
            return

        data.pop("full_name", None)

    def extract_explicit_name(self, text: str) -> str | None:
        value = (text or "").strip()
        candidates: list[str] = []
        for match in re.finditer(r"(?:me llamo|mi nombre es)\s+([^,.;!?]+)", value, re.I):
            prefix = value[max(0, match.start() - 4) : match.start()].lower()
            if re.search(r"no\s+$", prefix):
                continue
            candidates.append(match.group(1))

        soy_match = re.match(r"\s*soy\s+([^,.;!?]+)", value, re.I)
        if soy_match:
            candidates.append(soy_match.group(1))

        for candidate in reversed(candidates):
            candidate = re.split(
                r"\s+y\s+(?=quiero|necesito|busco|deseo|solicito|tengo|gano|trabajo)",
                candidate,
                maxsplit=1,
                flags=re.I,
            )[0]
            name = self.extract_name(candidate)
            if name:
                return name
        return None

    @staticmethod
    def is_name_denial(text: str) -> bool:
        normalized = (text or "").lower()
        return bool(
            re.search(
                r"\b(?:no\s+me\s+llamo|ese\s+no\s+es\s+mi\s+nombre|"
                r"mi\s+nombre\s+no\s+es|no\s+es\s+mi\s+nombre)\b",
                normalized,
            )
        )

    @staticmethod
    def _looks_like_bare_name(text: str) -> bool:
        return not bool(re.search(r"[,.;!?\d]", (text or "").strip()))

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

    @staticmethod
    def extract_integer(text: str) -> int | None:
        match = re.search(r"\d+", (text or "").strip())
        return int(match.group(0)) if match else None

    def clear_invalid_customer_name(self, customer) -> bool:
        full_name = (getattr(customer, "full_name", "") or "").strip()
        if not full_name or self.credit_service.is_valid_person_name(full_name):
            return False

        customer.full_name = None
        return True
