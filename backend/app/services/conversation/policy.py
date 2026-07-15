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
        return ai_data.get("intent") == "asesor" or any(
            word in (text or "").lower() for word in cls.HANDOFF_WORDS
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

    @staticmethod
    def welcome_response() -> str:
        return (
            "Hola, soy CrediBot. Te puedo ayudar con una precalificacion de credito, "
            "resolver dudas sobre requisitos o derivarte con un asesor. En que te puedo ayudar?"
        )
