from app.services.ai.groq_service import GroqService


class ExtractionService:
    def __init__(self):
        self.groq = GroqService()

    def extract_credit_data(self, text: str) -> dict:
        system_prompt = """
        Eres un extractor de datos para un chatbot financiero.
        Debes responder únicamente JSON válido.

        Extrae estos campos si existen:
        - intent: credito, asesor, saludo, desconocido
        - full_name
        - amount
        - term_months
        - monthly_income

        Reglas:
        - Si el usuario dice "tres años", term_months debe ser 36.
        - Si dice "cinco mil", amount debe ser 5000.
        - Si un dato no existe, usa null.
        """

        user_prompt = f"""
        Mensaje del usuario:
        {text}

        Devuelve JSON con esta forma:
        {{
            "intent": "credito | asesor | saludo | desconocido",
            "full_name": null,
            "amount": null,
            "term_months": null,
            "monthly_income": null
        }}
        """

        result = self.groq.generate_json(system_prompt, user_prompt)

        return {
            "intent": result.get("intent"),
            "full_name": result.get("full_name"),
            "amount": result.get("amount"),
            "term_months": result.get("term_months"),
            "monthly_income": result.get("monthly_income"),
        }