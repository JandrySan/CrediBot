from decimal import Decimal

from app.services.tools.base import Tool
from app.services.rules.credit_rule_engine import CreditRuleEngine


class CheckCreditRulesTool(Tool):
    @property
    def name(self) -> str:
        return "check_credit_rules"

    @property
    def description(self) -> str:
        return (
            "Evalúa una solicitud de crédito contra las reglas de negocio. "
            "Requiere monto, plazo en meses e ingresos mensuales. "
            "Retorna PREAPROBADO u OBSERVADO con el motivo."
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "amount": {
                    "type": "number",
                    "description": "Monto solicitado en dólares",
                },
                "term_months": {
                    "type": "integer",
                    "description": "Plazo en meses",
                },
                "monthly_income": {
                    "type": "number",
                    "description": "Ingresos mensuales en dólares",
                },
            },
            "required": ["amount", "term_months", "monthly_income"],
        }

    def run(self, **kwargs) -> dict:
        engine = CreditRuleEngine()
        result = engine.evaluate(
            amount=Decimal(str(kwargs["amount"])),
            term_months=int(kwargs["term_months"]),
            monthly_income=Decimal(str(kwargs["monthly_income"])),
        )
        return result


class CalculatePaymentTool(Tool):
    @property
    def name(self) -> str:
        return "calculate_monthly_payment"

    @property
    def description(self) -> str:
        return (
            "Calcula la cuota mensual aproximada de un crédito "
            "dado el monto, plazo en meses y tasa de interés anual."
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "amount": {
                    "type": "number",
                    "description": "Monto del crédito en dólares",
                },
                "term_months": {
                    "type": "integer",
                    "description": "Plazo en meses",
                },
                "annual_rate": {
                    "type": "number",
                    "description": "Tasa de interés anual en porcentaje (ej: 15 para 15%)",
                },
            },
            "required": ["amount", "term_months", "annual_rate"],
        }

    def run(self, **kwargs) -> dict:
        amount = float(kwargs["amount"])
        term = int(kwargs["term_months"])
        rate = float(kwargs["annual_rate"]) / 100 / 12

        if rate == 0:
            payment = amount / term
        else:
            payment = amount * (rate * (1 + rate) ** term) / ((1 + rate) ** term - 1)

        total = payment * term
        interest = total - amount

        return {
            "monthly_payment": round(payment, 2),
            "total_payment": round(total, 2),
            "total_interest": round(interest, 2),
        }
