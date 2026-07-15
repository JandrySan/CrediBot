from app.services.ai.ai_gateway import AIGateway

CONSULTA_KEYWORDS = [
    "regla",
    "reglas",
    "politica",
    "política",
    "requisito",
    "requisitos",
    "tasa",
    "interes",
    "interés",
    "intereses",
    "condicion",
    "condición",
    "documento",
    "documentos",
    "plazo",
    "maximo",
    "máximo",
    "anticipado",
    "como funciona",
    "que necesito",
    "me puedes decir",
    "podrias",
    "que es",
    "cual es",
    "cuales son",
    "pregunta",
    "consulta",
]


class IntentDetector:
    def __init__(self):
        self.ai = AIGateway()

    def detect(self, text: str) -> str:
        system_prompt = """
        Eres un clasificador de intención para CrediBot.
        Responde únicamente JSON válido.

        Intenciones permitidas:
        - saludo
        - credito
        - asesor
        - consulta
        - desconocido

        Reglas:
        - "saludo": el usuario solo saluda sin pedir nada
        - "credito": el usuario da datos o expresa interes en un credito
        - "asesor": el usuario pide hablar con un humano
        - "consulta": el usuario pregunta sobre reglas, politicas, requisitos, tasas, plazos, documentos o condiciones
        - "desconocido": cualquier otra cosa
        """

        user_prompt = f"""
        Mensaje:
        {text}

        Devuelve:
        {{
            "intent": "saludo | credito | asesor | consulta | desconocido"
        }}
        """

        result = self.ai.generate_json(system_prompt, user_prompt)
        intent = result.get("intent")

        if intent:
            return intent

        return self._fallback(text)

    def _fallback(self, text: str) -> str:
        normalized = text.lower()

        if any(
            word in normalized for word in ["asesor", "humano", "persona", "agente", "ejecutivo"]
        ):
            return "asesor"

        if any(kw in normalized for kw in CONSULTA_KEYWORDS):
            return "consulta"

        if any(
            word in normalized for word in ["credito", "crédito", "prestamo", "préstamo", "dinero"]
        ):
            return "credito"

        if any(word in normalized for word in ["hola", "buenas", "buenos días", "buenas tardes"]):
            return "saludo"

        return "desconocido"
