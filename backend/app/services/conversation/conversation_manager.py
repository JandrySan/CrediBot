from decimal import Decimal, InvalidOperation
from sqlalchemy.orm import Session

from app.repositories.customer_repository import CustomerRepository
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.credit_application_repository import CreditApplicationRepository
from app.services.rules.credit_rule_engine import CreditRuleEngine
from app.state_machine.states import ConversationState


class ConversationManager:
    def __init__(self, db: Session):
        self.customer_repo = CustomerRepository(db)
        self.conversation_repo = ConversationRepository(db)
        self.message_repo = MessageRepository(db)
        self.application_repo = CreditApplicationRepository(db)
        self.rule_engine = CreditRuleEngine()

    def process_message(self, phone_number: str, text: str) -> str:
        text = (text or "").strip()

        customer = self.customer_repo.get_or_create(phone_number)
        conversation = self.conversation_repo.get_or_create_active(customer.id)

        self.message_repo.save_message(
            conversation_id=conversation.id,
            direction="INBOUND",
            content=text,
            message_type="TEXT"
        )

        if self._wants_human(text):
            response = (
                "Entendido. Te voy a derivar con un asesor humano. "
                "Por favor espera un momento."
            )
            self.conversation_repo.update_state(conversation, ConversationState.HANDOFF.value)
            conversation.status = "HANDOFF"
            self.conversation_repo.db.commit()
            self._save_outbound(conversation.id, response)
            return response

        state = conversation.current_state

        if state == ConversationState.START.value:
            response = (
                "Hola 👋 Soy CrediBot.\n\n"
                "Te ayudaré con una precalificación rápida de crédito.\n\n"
                "Para empezar, dime tu nombre completo."
            )
            self.conversation_repo.update_state(conversation, ConversationState.ASK_NAME.value)

        elif state == ConversationState.ASK_NAME.value:
            customer.full_name = text
            self.customer_repo.db.commit()

            response = (
                f"Mucho gusto, {text}.\n\n"
                "¿Qué monto deseas solicitar? Escribe solo el valor en dólares.\n"
                "Ejemplo: 3000"
            )
            self.conversation_repo.update_state(conversation, ConversationState.ASK_AMOUNT.value)

        elif state == ConversationState.ASK_AMOUNT.value:
            amount = self._parse_decimal(text)

            if amount is None or amount <= 0:
                response = "Por favor ingresa un monto válido. Ejemplo: 3000"
            else:
                application = self.application_repo.get_or_create_latest(customer.id)
                self.application_repo.update(application, amount=amount)

                response = (
                    "Perfecto.\n\n"
                    "¿En cuántos meses deseas pagar el crédito?\n"
                    "Ejemplo: 24"
                )
                self.conversation_repo.update_state(conversation, ConversationState.ASK_TERM.value)

        elif state == ConversationState.ASK_TERM.value:
            try:
                term_months = int(text)
            except ValueError:
                term_months = None

            if term_months is None or term_months <= 0:
                response = "Por favor ingresa un plazo válido en meses. Ejemplo: 24"
            else:
                application = self.application_repo.get_or_create_latest(customer.id)
                self.application_repo.update(application, term_months=term_months)

                response = (
                    "Gracias.\n\n"
                    "Ahora dime tus ingresos mensuales aproximados en dólares.\n"
                    "Ejemplo: 1200"
                )
                self.conversation_repo.update_state(conversation, ConversationState.ASK_INCOME.value)

        elif state == ConversationState.ASK_INCOME.value:
            income = self._parse_decimal(text)

            if income is None or income <= 0:
                response = "Por favor ingresa un ingreso válido. Ejemplo: 1200"
            else:
                application = self.application_repo.get_or_create_latest(customer.id)
                self.application_repo.update(application, monthly_income=income)

                evaluation = self.rule_engine.evaluate(
                    amount=Decimal(application.amount),
                    term_months=application.term_months,
                    monthly_income=income
                )

                self.application_repo.update(
                    application,
                    result=evaluation["result"],
                    reason=evaluation["reason"]
                )

                conversation.result = evaluation["result"]
                self.conversation_repo.update_state(conversation, ConversationState.SHOW_RESULT.value)

                response = (
                    f"Resultado de precalificación: {evaluation['result']}.\n\n"
                    f"Motivo: {evaluation['reason']}\n\n"
                    "Este resultado es preliminar.\n"
                    "Puedes escribir *asesor* en cualquier momento para hablar con una persona."
                )

        else:
            response = (
                "Tu solicitud ya fue registrada.\n\n"
                "Escribe *asesor* si deseas hablar con una persona."
            )

        self._save_outbound(conversation.id, response)
        return response

    def _save_outbound(self, conversation_id: int, response: str):
        self.message_repo.save_message(
            conversation_id=conversation_id,
            direction="OUTBOUND",
            content=response,
            message_type="TEXT"
        )

    def _parse_decimal(self, value: str):
        try:
            clean_value = value.replace("$", "").replace(",", ".").strip()
            return Decimal(clean_value)
        except (InvalidOperation, AttributeError):
            return None

    def _wants_human(self, text: str) -> bool:
        normalized = text.lower().strip()
        keywords = ["asesor", "humano", "persona", "agente", "ejecutivo"]
        return any(keyword in normalized for keyword in keywords)