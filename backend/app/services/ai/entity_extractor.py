from app.services.ai.ai_gateway import AIGateway


class EntityExtractor:
    def __init__(self):
        self.ai = AIGateway()

    def extract_credit_entities(self, text: str) -> dict:
        system_prompt = """
        Eres un extractor de entidades para una precalificacion de credito.
        Responde unicamente JSON valido.

        Extrae:
        - product_code: CONSUMO_PERSONAL_DEMO o MICROCREDITO_MINORISTA_DEMO
        - national_id: cedula simulada de 10 digitos si aparece
        - full_name
        - age
        - employment_status: EMPLOYED, SELF_EMPLOYED, RETIRED, UNEMPLOYED o STUDENT
        - employment_tenure: antiguedad laboral o del negocio en meses
        - amount
        - term_months
        - monthly_income
        - other_monthly_income
        - monthly_expenses
        - existing_debt_payments
        - pep_status: PEP, NOT_PEP o UNKNOWN
        - purpose

        Reglas:
        - "tres anos" equivale a 36 meses.
        - "dos anos" equivale a 24 meses.
        - "cinco mil" equivale a 5000.
        - Si un dato no existe, usa null.
        """

        user_prompt = f"""
        Mensaje:
        {text}

        Devuelve:
        {{
            "national_id": null,
            "product_code": null,
            "full_name": null,
            "age": null,
            "employment_status": null,
            "employment_tenure": null,
            "amount": null,
            "term_months": null,
            "monthly_income": null,
            "other_monthly_income": null,
            "monthly_expenses": null,
            "existing_debt_payments": null,
            "pep_status": null,
            "purpose": null
        }}
        """

        result = self.ai.generate_json(system_prompt, user_prompt)

        return {
            "product_code": result.get("product_code"),
            "national_id": result.get("national_id"),
            "full_name": result.get("full_name"),
            "age": result.get("age"),
            "employment_status": result.get("employment_status"),
            "employment_tenure": result.get("employment_tenure"),
            "amount": result.get("amount"),
            "term_months": result.get("term_months"),
            "monthly_income": result.get("monthly_income"),
            "other_monthly_income": result.get("other_monthly_income"),
            "monthly_expenses": result.get("monthly_expenses"),
            "existing_debt_payments": result.get("existing_debt_payments"),
            "pep_status": result.get("pep_status"),
            "purpose": result.get("purpose"),
        }
