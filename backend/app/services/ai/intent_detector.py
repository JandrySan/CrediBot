from app.services.ai.ai_gateway import AIGateway


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
        - desconocido
        """

        user_prompt = f"""
        Mensaje:
        {text}

        Devuelve:
        {{
            "intent": "saludo | credito | asesor | desconocido"
        }}
        """

        result = self.ai.generate_json(system_prompt, user_prompt)
        intent = result.get("intent")

        if intent:
            return intent

        return self._fallback(text)

    def _fallback(self, text: str) -> str:
        normalized = text.lower()

        if any(word in normalized for word in ["asesor", "humano", "persona", "agente", "ejecutivo"]):
            return "asesor"

        if any(word in normalized for word in ["credito", "crédito", "prestamo", "préstamo", "dinero"]):
            return "credito"

        if any(word in normalized for word in ["hola", "buenas", "buenos días", "buenas tardes"]):
            return "saludo"

        return "desconocido"