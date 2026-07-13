import re
import unicodedata


class ResponseModePreference:
    AUDIO = "AUDIO"
    TEXT = "TEXT"

    AUDIO_PATTERNS = (
        r"\b(responde|respondeme|contestame|mandame|enviame|enviar|manda|envia)\b.*\b(audio|voz|nota de voz)\b",
        r"\b(audio|voz|nota de voz)\b.*\b(respuesta|respuestas|responder|contestame|mandame|enviame)\b",
        r"\bmodo audio\b",
        r"\bpor audio\b",
        r"\ben audio\b",
        r"\ben voz\b",
        r"\bquiero audio\b",
        r"\bquiero voz\b",
    )
    TEXT_PATTERNS = (
        r"\b(responde|respondeme|contestame|mandame|enviame|enviar|manda|envia|escribe)\b.*\b(texto|escrito)\b",
        r"\b(texto|escrito)\b.*\b(respuesta|respuestas|responder|contestame|mandame|enviame)\b",
        r"\bmodo texto\b",
        r"\bpor texto\b",
        r"\ben texto\b",
        r"\bsolo texto\b",
        r"\bquiero texto\b",
        r"\bpor escrito\b",
    )
    AUDIO_COMMANDS = {
        "audio",
        "modo audio",
        "responde audio",
        "responde en audio",
        "respondeme audio",
        "respondeme en audio",
        "contestame en audio",
        "por audio",
        "en audio",
        "quiero audio",
        "quiero voz",
        "nota de voz",
    }
    TEXT_COMMANDS = {
        "texto",
        "modo texto",
        "responde texto",
        "responde en texto",
        "respondeme texto",
        "respondeme en texto",
        "contestame en texto",
        "por texto",
        "en texto",
        "solo texto",
        "quiero texto",
        "por escrito",
    }
    BUSINESS_CONTENT_KEYWORDS = {
        "asesor",
        "credito",
        "creditos",
        "prestamo",
        "prestamos",
        "solicitar",
        "solicito",
        "monto",
        "dolares",
        "plazo",
        "mes",
        "meses",
        "ingreso",
        "ingresos",
        "requisito",
        "requisitos",
        "tasa",
        "interes",
        "documento",
        "documentos",
    }

    @classmethod
    def detect(cls, text: str) -> str | None:
        normalized = cls.normalize(text)
        if not normalized:
            return None

        if any(re.search(pattern, normalized) for pattern in cls.TEXT_PATTERNS):
            return cls.TEXT

        if any(re.search(pattern, normalized) for pattern in cls.AUDIO_PATTERNS):
            return cls.AUDIO

        return None

    @classmethod
    def is_command_only(cls, text: str, response_mode: str | None) -> bool:
        normalized = cls.normalize(text)
        if not normalized or not response_mode:
            return False

        if response_mode == cls.AUDIO:
            return normalized in cls.AUDIO_COMMANDS or cls._is_preference_only_request(
                normalized,
                cls.AUDIO_PATTERNS,
            )

        if response_mode == cls.TEXT:
            return normalized in cls.TEXT_COMMANDS or cls._is_preference_only_request(
                normalized,
                cls.TEXT_PATTERNS,
            )

        return False

    @classmethod
    def _is_preference_only_request(cls, normalized: str, patterns: tuple[str, ...]) -> bool:
        if not any(re.search(pattern, normalized) for pattern in patterns):
            return False

        if re.search(r"\d", normalized):
            return False

        return not any(
            keyword in normalized
            for keyword in cls.BUSINESS_CONTENT_KEYWORDS
        )

    @staticmethod
    def normalize(text: str) -> str:
        value = (text or "").strip().lower()
        if not value:
            return ""

        value = "".join(
            char
            for char in unicodedata.normalize("NFD", value)
            if unicodedata.category(char) != "Mn"
        )
        value = re.sub(r"[^a-z0-9\s]", " ", value)
        return re.sub(r"\s+", " ", value).strip()
