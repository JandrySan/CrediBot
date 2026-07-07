from decimal import Decimal, InvalidOperation
from sqlalchemy.orm import Session

from app.repositories.customer_repository import CustomerRepository
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.credit_application_repository import CreditApplicationRepository
from app.services.rules.credit_rule_engine import CreditRuleEngine
from app.services.ai.ai_orchestrator import AIOrchestrator
from app.state_machine.states import ConversationState


class ConversationManager:
    def __init__(self, db: Session):
        self.customer_repo = CustomerRepository(db)
        self.conversation_repo = ConversationRepository(db)
        self.message_repo = MessageRepository(db)
        self.application_repo = CreditApplicationRepository(db)
        self.rule_engine = CreditRuleEngine()
        self.ai = AIOrchestrator()

    def process_message(self, phone_number: str, text: str) -> str:
        text = (text or "").strip()

        customer = self.customer_repo.get_or_create(phone_number)
        conversation = self.conversation_repo.get_or_create_active(customer.id)
        application = self.application_repo.get_or_create_latest(customer.id)

        self.message_repo.save_message(
            conversation_id=conversation.id,
            direction="INBOUND",
            content=text,
            message_type="TEXT"
        )

        ai_data = self.ai.analyze_message(text)

        if ai_data.get("intent") == "asesor" or self._wants_human(text):
            response = self._handoff(conversation)
            self._save_outbound(conversation.id, response)
            return response

        self._apply_ai_data(customer, application, ai_data)

        response = self._build_response(customer, conversation, application)

        response = self.ai.improve_response(response)

        self._save_outbound(conversation.id, response)
        return response

    def _apply_ai_data(self, customer, application, ai_data: dict):
        if ai_data.get("full_name") and not customer.full_name:
            customer.full_name = ai_data["full_name"]
            self.customer_repo.db.commit()

        if ai_data.get("amount") and application.amount is None:
            application.amount = Decimal(str(ai_data["amount"]))

        if ai_data.get("term_months") and application.term_months is None:
            application.term_months = int(ai_data["term_months"])

        if ai_data.get("monthly_income") and application.monthly_income is None:
            application.monthly_income = Decimal(str(ai_data["monthly_income"]))

        self.application_repo.db.commit()

    def _build_response(self, customer, conversation, application) -> str:
        if conversation.current_state == ConversationState.START.value:
            self.conversation_repo.update_state(conversation, ConversationState.ASK_NAME.value)

        if not customer.full_name:
            return (
                "Hola 👋 Soy CrediBot.\n\n"
                "Te ayudaré con una precalificación rápida de crédito.\n\n"
                "Para empezar, dime tu nombre completo."
            )

        if not application.amount:
            self.conversation_repo.update_state(conversation, ConversationState.ASK_AMOUNT.value)
            return (
                f"Mucho gusto, {customer.full_name}.\n\n"
                "¿Qué monto deseas solicitar? Escribe el valor en dólares."
            )

        if not application.term_months:
            self.conversation_repo.update_state(conversation, ConversationState.ASK_TERM.value)
            return (
                "Perfecto.\n\n"
                "¿En cuántos meses deseas pagar el crédito?"
            )

        if not application.monthly_income:
            self.conversation_repo.update_state(conversation, ConversationState.ASK_INCOME.value)
            return (
                "Gracias.\n\n"
                "Ahora dime tus ingresos mensuales aproximados en dólares."
            )

        if not application.result:
            evaluation = self.rule_engine.evaluate(
                amount=Decimal(application.amount),
                term_months=application.term_months,
                monthly_income=Decimal(application.monthly_income)
            )

            self.application_repo.update(
                application,
                result=evaluation["result"],
                reason=evaluation["reason"]
            )

            conversation.result = evaluation["result"]
            self.conversation_repo.update_state(conversation, ConversationState.SHOW_RESULT.value)

            return (
                f"Resultado de precalificación: {evaluation['result']}.\n\n"
                f"Motivo: {evaluation['reason']}\n\n"
                "Este resultado es preliminar. Puedes escribir asesor en cualquier momento."
            )

        return (
            "Tu solicitud ya fue registrada.\n\n"
            "Escribe asesor si deseas hablar con una persona."
        )

    def _handoff(self, conversation) -> str:
        self.conversation_repo.update_state(conversation, ConversationState.HANDOFF.value)
        conversation.status = "HANDOFF"
        self.conversation_repo.db.commit()

        return (
            "Entendido. Te voy a derivar con un asesor humano. "
            "Por favor espera un momento."
        )

    def _save_outbound(self, conversation_id: int, response: str):
        self.message_repo.save_message(
            conversation_id=conversation_id,
            direction="OUTBOUND",
            content=response,
            message_type="TEXT"
        )

    def _wants_human(self, text: str) -> bool:
        normalized = text.lower().strip()
        keywords = ["asesor", "humano", "persona", "agente", "ejecutivo"]
        return any(keyword in normalized for keyword in keywords)