from app.services.ai.ai_gateway import AIGateway


class EntityExtractor:
    def __init__(self):
        self.ai = AIGateway()

    def extract_credit_entities(self, text: str) -> dict:
        system_prompt = """
        Eres un extractor de entidades para una precalificación de crédito.
        Responde únicamente JSON válido.

        Extrae:
        - full_name
        - amount
        - term_months
        - monthly_income

        Reglas:
        - "tres años" equivale a 36 meses.
        - "dos años" equivale a 24 meses.
        - "cinco mil" equivale a 5000.
        - Si un dato no existe, usa null.
        """

        user_prompt = f"""
        Mensaje:
        {text}

        Devuelve:
        {{
            "full_name": null,
            "amount": null,
            "term_months": null,
            "monthly_income": null
        }}
        """

        result = self.ai.generate_json(system_prompt, user_prompt)

        return {
            "full_name": result.get("full_name"),
            "amount": result.get("amount"),
            "term_months": result.get("term_months"),
            "monthly_income": result.get("monthly_income"),
        }