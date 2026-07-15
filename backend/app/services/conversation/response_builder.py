import re


class ConversationResponseBuilder:
    """Construye respuestas deterministas sin acceder a red ni base de datos."""

    def question_for_field(self, field: str, customer, application) -> str:
        if field == "national_id":
            return (
                "Hola, que gusto saludarte. Soy CrediBot y te ayudare con tu "
                "precalificacion de credito. Para revisar tu perfil en la central de "
                "riesgo simulada, me compartes tu cedula de 10 digitos?"
            )
        if field == "full_name":
            return (
                "Gracias. No encontre un nombre asociado a esa cedula en la central "
                "simulada. Me compartes tu nombre completo?"
            )
        if field == "amount":
            return self._amount_question(customer)
        if field == "term_months":
            return self._term_question(application)
        if field == "monthly_income":
            return self._income_question(application)
        return "Cuentame un poco mas para poder ayudarte mejor con tu solicitud."

    @staticmethod
    def _amount_question(customer) -> str:
        if customer.full_name:
            return (
                f"Es un gusto hablar contigo, {customer.full_name}. "
                "Para continuar con tu precalificacion, que monto deseas solicitar en dolares?"
            )
        return "Perfecto, para avanzar dime que monto deseas solicitar en dolares."

    def _term_question(self, application) -> str:
        if application.amount is not None:
            return (
                f"Excelente, ya tengo registrado un monto de {self.format_currency(application.amount)}. "
                "Ahora cuentame en cuantos meses te gustaria pagarlo."
            )
        return "Perfecto, en cuantos meses te gustaria pagar el credito?"

    def _income_question(self, application) -> str:
        details = []
        if application.amount is not None:
            details.append(f"un monto de {self.format_currency(application.amount)}")
        if application.term_months is not None:
            details.append(f"un plazo de {application.term_months} meses")

        if details:
            return (
                f"Super, ya tengo {self.human_join(details)}. Para cerrar tu "
                "precalificacion, cual es tu ingreso mensual aproximado en dolares?"
            )
        return (
            "Gracias. Para cerrar tu precalificacion, cual es tu ingreso mensual "
            "aproximado en dolares?"
        )

    def build_result_response(self, evaluation: dict, customer, application) -> str:
        profile_details = self.profile_snapshot(customer, application)
        result_label = self.human_result_label(evaluation.get("result"))
        reason = (evaluation.get("reason") or "").strip()
        prefix = (
            f"Listo, con la informacion que me compartiste ({profile_details}), "
            if profile_details
            else "Listo, "
        )
        return (
            f"{prefix}tu resultado preliminar es {result_label}. Motivo: {reason}. "
            "Si deseas, tambien puedo derivarte con un asesor humano."
        )

    def build_already_registered_response(self, customer, application) -> str:
        profile_details = self.profile_snapshot(customer, application)
        if profile_details:
            return (
                f"Tu solicitud ya fue registrada con estos datos: {profile_details}. "
                "Si quieres continuar o ajustar algo, lo revisamos juntos. Tambien "
                "puedes escribir asesor para hablar con una persona."
            )
        return (
            "Tu solicitud ya fue registrada. Si quieres, tambien puedo derivarte con "
            "un asesor humano."
        )

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
            "OBSERVADO": "observado",
            "RECHAZADO": "rechazado",
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
