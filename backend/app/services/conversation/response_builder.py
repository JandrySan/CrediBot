import re


class ConversationResponseBuilder:
    """Construye respuestas deterministas sin acceder a red ni base de datos."""

    def question_for_field(
        self,
        field: str,
        customer,
        application,
        suggested_value=None,
    ) -> str:
        if field == "privacy_consent":
            return "¿Aceptas usar tus datos para esta precalificacion? Responde si o no."
        if field == "product_code":
            return (
                "¿Para que necesitas el credito: gastos personales o tu negocio? "
                "Responde personal o negocio."
            )
        if field == "national_id":
            return (
                "Escribe tu cedula de 10 digitos. La usare para identificar la solicitud; "
                "antes de revisar el historial te pedire autorizacion."
            )
        if field == "bureau_consent":
            return "¿Autorizas revisar tu historial simulado? Responde si o no."
        if field == "full_name":
            if suggested_value:
                return (
                    f"Encontre el nombre {suggested_value}. ¿Es correcto? "
                    "Responde si o escribe tu nombre completo."
                )
            return "¿Cual es tu nombre completo? Por ejemplo: Maria Lopez."
        if field == "age":
            return "¿Que edad tienes? Puedes responder, por ejemplo: 35 años."
        if field == "employment_status":
            return (
                "¿De donde vienen principalmente tus ingresos: empleo, negocio propio, "
                "jubilacion u otra fuente?"
            )
        if field == "employment_tenure":
            return (
                "¿Cuanto tiempo llevas en ese empleo o negocio? Puedes responder en meses o años."
            )
        if field == "amount":
            return self._amount_question(customer)
        if field == "term_months":
            return self._term_question(application)
        if field == "monthly_income":
            return self._income_question(application)
        if field == "monthly_expenses":
            return (
                "Sin contar deudas, ¿cuanto gastas al mes en vivienda, comida, servicios "
                "y otros gastos del hogar?"
            )
        if field == "existing_debt_payments":
            return (
                "¿Cuanto pagas al mes por tarjetas, prestamos u otras deudas? "
                "Si no tienes, responde 0."
            )
        if field == "pep_status":
            return (
                "¿Tu o un familiar cercano ocupa, u ocupo recientemente, un cargo publico "
                "importante? Responde si, no o no estoy seguro."
            )
        return "Cuentame un poco mas para poder ayudarte mejor con tu solicitud."

    @staticmethod
    def name_correction_question() -> str:
        return (
            "Gracias por corregirme. ¿Cual es tu nombre completo? "
            "Puedes escribir, por ejemplo: Me llamo Maria Lopez."
        )

    @staticmethod
    def _amount_question(customer) -> str:
        if customer.full_name:
            return (
                f"Perfecto, {customer.full_name}. ¿Cuanto dinero necesitas? "
                "Por ejemplo: 5000 dolares."
            )
        return "¿Cuanto dinero necesitas? Por ejemplo: 5000 dolares."

    def _term_question(self, application) -> str:
        if application.amount is not None:
            return (
                f"Tengo el monto: {self.format_currency(application.amount)}. "
                "¿En cuantos meses te gustaria pagarlo?"
            )
        return "¿En cuantos meses te gustaria pagar el credito?"

    def _income_question(self, application) -> str:
        details = []
        if application.amount is not None:
            details.append(f"un monto de {self.format_currency(application.amount)}")
        if application.term_months is not None:
            details.append(f"un plazo de {application.term_months} meses")

        if details:
            return f"Ya tengo {self.human_join(details)}. ¿Cuanto recibes al mes, aproximadamente?"
        return "¿Cuanto recibes al mes, aproximadamente?"

    def build_result_response(self, evaluation: dict, customer, application) -> str:
        del customer
        result_label = self.human_result_label(evaluation.get("result"))
        installment = evaluation.get("estimated_installment")
        summary_parts = []
        if application.amount is not None:
            summary_parts.append(self.format_currency(application.amount))
        if application.term_months is not None:
            summary_parts.append(f"{application.term_months} meses")
        summary = " a ".join(summary_parts)

        lines = [
            f"Ya hice la simulacion{f' para {summary}' if summary else ''}.",
            f"Resultado: {result_label}.",
        ]
        if installment is not None:
            lines.insert(1, f"Cuota estimada: {self.format_currency(installment)} al mes.")

        reasons = self._friendly_result_reasons(evaluation)
        if reasons:
            lines.append("Lo mas importante:")
            lines.extend(f"• {reason}" for reason in reasons)

        if (evaluation.get("result") or "").upper() == "PREQUALIFIED":
            lines.append("Es una orientacion inicial; la aprobacion requiere verificacion final.")
        else:
            lines.append(
                "No es una decision final. Puedes corregir un dato, pedir una explicacion "
                "o hablar con un asesor."
            )
        return "\n".join(lines)

    def build_already_registered_response(self, customer, application) -> str:
        del customer, application
        return (
            "La simulacion ya esta registrada. Puedes decirme que dato quieres cambiar, "
            "pedirme una explicacion o escribir asesor."
        )

    @classmethod
    def _friendly_result_reasons(cls, evaluation: dict) -> list[str]:
        labels = {
            "AMOUNT_IN_RANGE": "El monto esta fuera del rango del producto.",
            "TERM_IN_RANGE": "El plazo esta fuera del rango del producto.",
            "AGE_REQUIRED": "Falta confirmar la edad.",
            "MINIMUM_AGE": "La edad no cumple el minimo del producto.",
            "MAXIMUM_AGE_AT_MATURITY": "La edad al finalizar el credito requiere revision.",
            "IDENTITY_VERIFIED": "Falta verificar tu identidad.",
            "PEP_STATUS_REQUIRED": "Falta responder la pregunta sobre cargos publicos.",
            "PEP_REVIEW": "La condicion declarada requiere revision de un asesor.",
            "INCOME_REQUIRED": "Falta confirmar el ingreso mensual.",
            "MINIMUM_MONTHLY_INCOME": "El ingreso esta por debajo del minimo del producto.",
            "EXPENSES_REQUIRED": "Falta indicar los gastos mensuales.",
            "EXPENSES_DECLARED": "Los gastos declarados necesitan revision.",
            "MAXIMUM_PROJECTED_DTI": "La suma de cuotas seria alta frente al ingreso.",
            "MINIMUM_DISPOSABLE_AFTER_PAYMENT": (
                "El dinero disponible despues de gastos y cuotas seria insuficiente."
            ),
            "JOB_TENURE_REQUIRED": "Falta indicar la antiguedad en el empleo.",
            "BUSINESS_TENURE_REQUIRED": "Falta indicar la antiguedad del negocio.",
            "MINIMUM_EMPLOYMENT_TENURE": "La antiguedad laboral requiere revision.",
            "MINIMUM_BUSINESS_TENURE": "La antiguedad del negocio requiere revision.",
            "CREDIT_HISTORY_REQUIRED": "No hay historial suficiente para evaluar.",
            "MINIMUM_CREDIT_SCORE": "El puntaje del historial requiere revision.",
            "NO_ACTIVE_SEVERE_DELINQUENCY": "Hay una mora importante en el historial.",
            "MAXIMUM_RECENT_INQUIRIES": "Hay varias consultas recientes en el historial.",
        }
        failures = [item for item in evaluation.get("rule_results", []) if not item.get("passed")]
        priorities = {"NOT_PREQUALIFIED": 0, "MANUAL_REVIEW": 1, "NEEDS_INFORMATION": 2}
        failures.sort(key=lambda item: priorities.get(item.get("outcome"), 3))

        reasons: list[str] = []
        for item in failures:
            code = item.get("code")
            reason = labels.get(code) or (item.get("explanation") or "").strip()
            if reason and reason not in reasons:
                reasons.append(reason)
            if len(reasons) == 3:
                break
        if reasons:
            return reasons

        fallback = (evaluation.get("reason") or "").strip()
        return [fallback] if fallback else []

    def profile_snapshot(self, customer, application) -> str:
        details: list[str] = []
        if customer.full_name:
            details.append(f"nombre {customer.full_name}")
        if getattr(customer, "national_id", None):
            details.append(f"cedula {customer.national_id}")
        if application.amount is not None:
            details.append(f"monto de {self.format_currency(application.amount)}")
        if application.term_months is not None:
            details.append(f"plazo de {application.term_months} meses")
        if application.monthly_income is not None:
            details.append(
                f"ingresos mensuales de {self.format_currency(application.monthly_income)}"
            )
        return self.human_join(details)

    @staticmethod
    def human_result_label(result: str | None) -> str:
        normalized = (result or "").strip().upper()
        labels = {
            "PREAPROBADO": "preaprobado",
            "PREQUALIFIED": "precalificado de forma informativa",
            "OBSERVADO": "observado",
            "RECHAZADO": "rechazado",
            "NOT_PREQUALIFIED": "no precalificado por el momento",
            "MANUAL_REVIEW": "pendiente de revision humana",
            "NEEDS_INFORMATION": "pendiente de informacion o verificacion",
            "SIMULATION_ONLY": "simulacion informativa",
            "ERROR": "no disponible por el momento",
        }
        return labels.get(normalized, normalized.lower() if normalized else "sin resultado")

    @staticmethod
    def human_join(items: list[str]) -> str:
        clean_items = [item.strip() for item in items if (item or "").strip()]
        if len(clean_items) < 2:
            return clean_items[0] if clean_items else ""
        if len(clean_items) == 2:
            return f"{clean_items[0]} y {clean_items[1]}"
        return f"{', '.join(clean_items[:-1])} y {clean_items[-1]}"

    @staticmethod
    def sanitize(response: str, user_text: str) -> str:
        cleaned = (response or "").strip()
        if not cleaned:
            return cleaned

        normalized_user = (user_text or "").lower()
        user_thanked = any(
            token in normalized_user for token in ("gracias", "agradezco", "thank you", "thanks")
        )
        if not user_thanked:
            cleaned = re.sub(
                r"^\s*(de nada|no hay de que|con gusto|a la orden|encantado de ayudarte|un gusto ayudarte)[\s,:\-\.!]*",
                "",
                cleaned,
                flags=re.IGNORECASE,
            ).strip()

        cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
        return re.sub(r"\n{3,}", "\n\n", cleaned).strip()

    @staticmethod
    def format_currency(value) -> str:
        try:
            return f"${float(value):,.2f}"
        except (TypeError, ValueError):
            return str(value)
