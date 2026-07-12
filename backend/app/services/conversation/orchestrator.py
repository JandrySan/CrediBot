from sqlalchemy.orm import Session

from app.repositories.ai_analysis_repository import AIAnalysisRepository
from app.repositories.conversation_state_history_repository import ConversationStateHistoryRepository
from app.repositories.customer_repository import CustomerRepository
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.credit_application_repository import CreditApplicationRepository

from app.services.ai.ai_orchestrator import AIOrchestrator
from app.services.conversation.conversation_state_service import ConversationStateService
from app.services.conversation.credit_application_service import CreditApplicationService
from app.services.tools import tool_registry
from app.services.tools.rag_tools import SearchFAQTool
from app.services.rag.knowledge_base import KnowledgeBase

from app.state_machine.states import ConversationState
from app.models.message import Message


class ConversationOrchestrator:
    def __init__(self, db: Session):
        self.db = db

        self.customer_repo = CustomerRepository(db)
        self.conversation_repo = ConversationRepository(db)
        self.message_repo = MessageRepository(db)
        self.application_repo = CreditApplicationRepository(db)
        self.ai_analysis_repo = AIAnalysisRepository(db)
        self.state_history_repo = ConversationStateHistoryRepository(db)

        self.ai = AIOrchestrator()
        self.state_service = ConversationStateService()
        self.credit_service = CreditApplicationService()

        self.knowledge_base = KnowledgeBase(db)
        if self.knowledge_base.is_ready():
            faq_tool = SearchFAQTool(self.knowledge_base)
            tool_registry.register(faq_tool)

    def handle_text_message(self, phone_number: str, text: str) -> str:
        text = (text or "").strip()

        customer = self.customer_repo.get_or_create(phone_number)
        conversation = self.conversation_repo.get_or_create_active(customer.id)
        application = self.application_repo.get_or_create_latest(customer.id)

        self._save_message(conversation.id, "INBOUND", text)

        if conversation.status == "HANDOFF":
            response = (
                "Tu mensaje fue recibido. Un asesor humano te responderá en breve."
            )
            self._save_message(conversation.id, "OUTBOUND", response)
            return response

        ai_data = self.ai.analyze_message(text)

        self.ai_analysis_repo.save_analysis(
            conversation_id=conversation.id,
            intent=ai_data.get("intent"),
            extracted_data=ai_data,
            model_used=self.ai.get_model_name()
        )

        if self._is_handoff_requested(text, ai_data):
            response = self._handoff(conversation)
            self._save_message(conversation.id, "OUTBOUND", response)
            return response

        self.credit_service.apply_extracted_data(
            customer=customer,
            application=application,
            data=ai_data,
            db=self.db
        )

        evaluation = self.credit_service.evaluate_if_complete(application)

        if evaluation:
            self.application_repo.update(
                application,
                result=evaluation["result"],
                reason=evaluation["reason"]
            )

            conversation.result = evaluation["result"]
            self.db.commit()

            self._change_state(
                conversation=conversation,
                new_state=ConversationState.SHOW_RESULT.value,
                reason="Solicitud completa y evaluada"
            )

            base_response = self._build_result_response(evaluation)
            enriched = self._enrich_with_tools(base_response, text, conversation.id)
            response = self.ai.improve_response(enriched)
            self._save_message(conversation.id, "OUTBOUND", response)
            return response

        missing_field = self.state_service.get_next_required_field(
            customer,
            application
        )

        if missing_field:
            new_state = self.state_service.state_for_missing_field(missing_field)

            self._change_state(
                conversation=conversation,
                new_state=new_state,
                reason=f"Falta el campo requerido: {missing_field}"
            )

            base_response = self._question_for_field(missing_field, customer)
            enriched = self._enrich_with_tools(base_response, text, conversation.id)
            response = self.ai.improve_response(enriched)
            self._save_message(conversation.id, "OUTBOUND", response)
            return response

        if ai_data.get("intent") in ("saludo", "desconocido"):
            enriched = self._enrich_with_tools(text, text, conversation.id)
            if enriched != text:
                response = self.ai.improve_response(enriched)
                self._save_message(conversation.id, "OUTBOUND", response)
                return response

        response = (
            "Tu solicitud ya fue registrada. "
            "Puedes escribir asesor si deseas hablar con una persona."
        )

        self._save_message(conversation.id, "OUTBOUND", response)
        return response

    def _enrich_with_tools(self, base_response: str, user_message: str, conversation_id: int) -> str:
        if not tool_registry.get_all():
            return base_response

        system_prompt = (
            "Eres CrediBot, un asistente financiero amable y profesional. "
            "Tienes acceso a herramientas que puedes usar para mejorar tu respuesta. "
            "Si el usuario hace una pregunta sobre créditos, busca en las FAQs. "
            "Si el usuario pide calcular una cuota, usa la calculadora. "
            "Responde de forma natural y conversacional."
        )

        history = self._build_message_history(conversation_id)

        tool_response = self.ai.process_with_tools(
            system_prompt=system_prompt,
            user_message=user_message,
            conversation_history=history,
            registry=tool_registry if tool_registry.get_all() else None,
        )

        if tool_response and len(tool_response) > len(base_response) * 0.5:
            return tool_response

        return base_response

    def _build_message_history(self, conversation_id: int) -> list[dict]:
        messages = (
            self.db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.id.asc())
            .limit(20)
            .all()
        )

        result = []
        for msg in messages:
            role = "user" if msg.direction == "INBOUND" else "assistant"
            result.append({"role": role, "content": msg.content})
        return result

    def _question_for_field(self, field: str, customer) -> str:
        questions = {
            "full_name": (
                "Hola 👋 Soy CrediBot. "
                "Te ayudaré con una precalificación rápida de crédito. "
                "Para empezar, dime tu nombre completo."
            ),
            "amount": (
                f"Mucho gusto, {customer.full_name}. "
                "¿Qué monto deseas solicitar? Escribe el valor en dólares."
            ),
            "term_months": (
                "Perfecto. ¿En cuántos meses deseas pagar el crédito?"
            ),
            "monthly_income": (
                "Gracias. Ahora dime tus ingresos mensuales aproximados en dólares."
            ),
        }

        return questions[field]

    def _build_result_response(self, evaluation: dict) -> str:
        return (
            f"Resultado de precalificación: {evaluation['result']}.\n\n"
            f"Motivo: {evaluation['reason']}\n\n"
            "Este resultado es preliminar. "
            "Puedes escribir asesor en cualquier momento para hablar con una persona."
        )

    def _handoff(self, conversation) -> str:
        self._change_state(
            conversation=conversation,
            new_state=ConversationState.HANDOFF.value,
            reason="Usuario solicitó hablar con asesor humano"
        )

        conversation.status = "HANDOFF"
        self.db.commit()

        return (
            "Entendido. Te voy a derivar con un asesor humano. "
            "Por favor espera un momento."
        )

    def _is_handoff_requested(self, text: str, ai_data: dict) -> bool:
        if ai_data.get("intent") == "asesor":
            return True

        normalized = text.lower()
        return any(
            word in normalized
            for word in ["asesor", "humano", "persona", "agente", "ejecutivo"]
        )

    def _save_message(self, conversation_id: int, direction: str, content: str):
        self.message_repo.save_message(
            conversation_id=conversation_id,
            direction=direction,
            content=content,
            message_type="TEXT"
        )

    def _change_state(self, conversation, new_state: str, reason: str):
        conversation, previous_state, changed = (
            self.conversation_repo.update_state_if_changed(
                conversation,
                new_state
            )
        )

        if changed:
            self.state_history_repo.save_transition(
                conversation_id=conversation.id,
                previous_state=previous_state,
                new_state=new_state,
                reason=reason
            )

        return conversation
