from decimal import Decimal


class CreditRuleEngine:
    def evaluate(self, amount: Decimal, term_months: int, monthly_income: Decimal) -> dict:
        if monthly_income < Decimal("600"):
            return {
                "result": "OBSERVADO",
                "reason": "Los ingresos mensuales son menores al mínimo requerido.",
            }

        if amount > monthly_income * Decimal("8"):
            return {
                "result": "OBSERVADO",
                "reason": "El monto solicitado supera la capacidad inicial estimada.",
            }

        if term_months > 60:
            return {
                "result": "OBSERVADO",
                "reason": "El plazo solicitado supera el máximo permitido.",
            }

        return {
            "result": "PREAPROBADO",
            "reason": "Cumple con las reglas básicas de precalificación.",
        }
