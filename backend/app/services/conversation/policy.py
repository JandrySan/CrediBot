import re
import unicodedata
from typing import ClassVar

from app.state_machine.states import ConversationState


class ConversationPolicy:
    HANDOFF_WORDS: ClassVar[tuple[str, ...]] = (
        "asesor",
        "humano",
        "persona",
        "agente",
        "ejecutivo",
    )
    FAQ_MARKERS: ClassVar[tuple[str, ...]] = (
        "?",
        "¿",
        "requisito",
        "documento",
        "politica",
        "política",
        "tasa",
        "interes",
        "interés",
        "condicion",
        "condición",
        "plazo maximo",
        "plazo máximo",
        "pago anticipado",
    )
    GREETINGS: ClassVar[frozenset[str]] = frozenset(
        {
            "hola",
            "buenas",
            "buen dia",
            "buenos dias",
            "buenas tardes",
            "buenas noches",
            "saludos",
            "hey",
            "hola buen dia",
            "hola buenos dias",
            "hola buenas",
            "hola buenas tardes",
            "hola buenas noches",
            "hola que tal",
        }
    )

    @classmethod
    def is_handoff_requested(cls, text: str, ai_data: dict) -> bool:
        if ai_data.get("intent") == "asesor":
            return True
        normalized = (text or "").lower()
        if any(
            re.search(rf"\b{re.escape(word)}\b", normalized)
            for word in ("asesor", "humano", "agente", "ejecutivo")
        ):
            return True
        return bool(
            re.search(
                r"\b(?:hablar|comunicarme|atencion)\b.{0,30}\bpersona(?:\s+real)?\b",
                normalized,
            )
        )

    @classmethod
    def should_send_welcome(
        cls,
        conversation,
        customer,
        application,
        text: str,
        ai_data: dict,
    ) -> bool:
        if conversation.current_state != ConversationState.START.value:
            return False
        if ai_data.get("intent") != "saludo" or not cls.is_plain_greeting(text):
            return False
        return not any(
            (
                bool(customer.full_name),
                application.amount is not None,
                application.term_months is not None,
                application.monthly_income is not None,
            )
        )

    @classmethod
    def is_plain_greeting(cls, text: str) -> bool:
        normalized = "".join(
            char
            for char in unicodedata.normalize("NFD", (text or "").lower().strip())
            if unicodedata.category(char) != "Mn"
        )
        normalized = re.sub(r"[^a-z\s]", " ", normalized)
        normalized = re.sub(r"\s+", " ", normalized).strip()
        return normalized in cls.GREETINGS

    @classmethod
    def is_faq_question(cls, text: str) -> bool:
        normalized = (text or "").lower().strip()
        return bool(normalized) and any(marker in normalized for marker in cls.FAQ_MARKERS)

    @classmethod
    def is_result_explanation_requested(cls, text: str) -> bool:
        raw = (text or "").strip().lower()
        if raw and all(character in {"?", "¿", " "} for character in raw):
            return True

        normalized = "".join(
            char
            for char in unicodedata.normalize("NFD", raw)
            if unicodedata.category(char) != "Mn"
        )
        normalized = re.sub(r"[^a-z\s]", " ", normalized)
        normalized = re.sub(r"\s+", " ", normalized).strip()
        if not normalized:
            return False

        markers = (
            "que paso",
            "q paso",
            "por que",
            "porque",
            "motivo",
            "razon",
            "explica",
            "explicacion",
            "no precalificado",
            "observado",
        )
        return any(marker in normalized for marker in markers)

    @staticmethod
    def welcome_response() -> str:
        return (
            "Hola, soy CrediBot. Puedo explicarte requisitos, hacer una simulacion de "
            "credito o comunicarte con un asesor.\n\n"
            "Escribe lo que necesitas. Por ejemplo: Quiero simular un credito."
        )
