from sqlalchemy.orm import Session

from app.config.settings import settings
from app.repositories.ai_analysis_repository import AIAnalysisRepository
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.conversation_state_history_repository import (
    ConversationStateHistoryRepository,
)
from app.repositories.credit_application_repository import CreditApplicationRepository
from app.repositories.customer_repository import CustomerRepository
from app.repositories.message_repository import MessageRepository
from app.services.ai.ai_orchestrator import AIOrchestrator
from app.services.conversation.conversation_state_service import ConversationStateService
from app.services.conversation.credit_application_service import CreditApplicationService
from app.services.conversation.faq_answer_service import FAQAnswerService
from app.services.conversation.history import build_ai_history
from app.services.conversation.input_extractor import ConversationInputExtractor
from app.services.conversation.policy import ConversationPolicy
from app.services.conversation.response_builder import ConversationResponseBuilder
from app.state_machine.states import ConversationState
from app.state_machine.transitions import can_transition


class ConversationOrchestrator:
    """Coordina un mensaje; delega extracción, políticas y presentación."""

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
        self.input_extractor = ConversationInputExtractor(
            self.state_service,
            self.credit_service,
        )
        self.responses = ConversationResponseBuilder()
        self.faq_service = FAQAnswerService(db, self.ai.response_generator)

    def handle_text_message(self, phone_number: str, text: str) -> str:
        return self._handle_message(phone_number, text, "TEXT")

    def handle_audio_message(self, phone_number: str, transcript_text: str) -> str:
        return self._handle_message(phone_number, transcript_text, "AUDIO")

    def _handle_message(
        self,
        phone_number: str,
        text: str,
        inbound_message_type: str,
    ) -> str:
        return self._process_message(
            phone_number=phone_number,
            text=(text or "").strip(),
            inbound_message_type=inbound_message_type,
        )

    def _process_message(
        self,
        phone_number: str,
        text: str,
        inbound_message_type: str,
    ) -> str:
        customer = self.customer_repo.get_or_create(phone_number)
        conversation = self.conversation_repo.get_or_create_active(customer.id)
        application = self.application_repo.get_or_create_latest(customer.id)
        self.input_extractor.clear_invalid_customer_name(customer)
        self._save_message(conversation.id, "INBOUND", text, inbound_message_type)

        if settings.AI_ONLY_MODE:
            return self._answer_with_ai(conversation.id, text)
        if conversation.status == "HANDOFF":
            return ""

        ai_data = self.input_extractor.enrich(
            conversation,
            customer,
            application,
            text,
            self.ai.analyze_message(text),
        )
        self.ai_analysis_repo.save_analysis(
            conversation_id=conversation.id,
            intent=ai_data.get("intent"),
            extracted_data=ai_data,
            model_used=self.ai.get_model_name(),
        )

        if ConversationPolicy.is_handoff_requested(text, ai_data):
            self._handoff(conversation)
            return ""
        if ConversationPolicy.should_send_welcome(
            conversation,
            customer,
            application,
            text,
            ai_data,
        ):
            return self._save_outbound(
                conversation.id,
                ConversationPolicy.welcome_response(),
            )
        if ai_data.get("intent") == "consulta":
            ai_response = self._generate_ai_response(conversation.id, text)
            if ai_response:
                return self._save_outbound(conversation.id, ai_response)

        faq_response = self.faq_service.answer(text)
        if faq_response:
            return self._save_outbound(conversation.id, faq_response)

        return self._continue_credit_flow(
            conversation,
            customer,
            application,
            text,
            ai_data,
        )

    def _continue_credit_flow(
        self,
        conversation,
        customer,
        application,
        text: str,
        ai_data: dict,
    ) -> str:
        self.credit_service.apply_extracted_data(customer, application, ai_data, self.db)
        evaluation = self.credit_service.evaluate_if_complete(
            application,
            customer=customer,
            db=self.db,
        )

        if evaluation:
            self.application_repo.update(
                application,
                result=evaluation["result"],
                reason=evaluation["reason"],
            )
            conversation.result = evaluation["result"]
            self._change_state(
                conversation,
                ConversationState.SHOW_RESULT.value,
                "Solicitud completa y evaluada",
            )
            response = self.responses.build_result_response(
                evaluation,
                customer,
                application,
            )
            return self._save_outbound(
                conversation.id,
                self._polish_response(response, text, use_ai=True),
            )

        missing_field = self.state_service.get_next_required_field(customer, application)
        if missing_field:
            self._change_state(
                conversation,
                self.state_service.state_for_missing_field(missing_field),
                f"Falta el campo requerido: {missing_field}",
            )
            question = self.responses.question_for_field(
                missing_field,
                customer,
                application,
            )
            return self._save_outbound(
                conversation.id,
                self._polish_response(question, text, use_ai=False),
            )

        response = self.responses.build_already_registered_response(customer, application)
        return self._save_outbound(
            conversation.id,
            self._polish_response(response, text, use_ai=True),
        )

    def _answer_with_ai(self, conversation_id: int, text: str) -> str:
        response = self._generate_ai_response(conversation_id, text)
        return self._save_outbound(conversation_id, response)

    def _generate_ai_response(self, conversation_id: int, text: str) -> str:
        history = build_ai_history(self.message_repo, conversation_id)
        if history and history[-1].get("role") == "user":
            history = history[:-1]
        return self.ai.generate_whatsapp_reply(text=text, history=history, db=self.db)

    def _handoff(self, conversation) -> None:
        self._change_state(
            conversation,
            ConversationState.HANDOFF.value,
            "Usuario solicito hablar con asesor humano",
        )
        conversation.status = "HANDOFF"
        self.db.flush()

    def _save_message(
        self,
        conversation_id: int,
        direction: str,
        content: str,
        message_type: str = "TEXT",
    ):
        return self.message_repo.save_message(
            conversation_id=conversation_id,
            direction=direction,
            content=content,
            message_type=message_type,
        )

    def _save_outbound(self, conversation_id: int, response: str) -> str:
        self._save_message(conversation_id, "OUTBOUND", response, "TEXT")
        return response

    def _change_state(self, conversation, new_state: str, reason: str):
        current = conversation.current_state
        if current != new_state and not can_transition(current, new_state):
            allowed = self.state_service.get_allowed_transition_names(current)
            raise ValueError(
                f"Transicion invalida: {current} -> {new_state}. Transiciones permitidas: {allowed}"
            )

        conversation, previous_state, changed = self.conversation_repo.update_state_if_changed(
            conversation, new_state
        )
        if changed:
            self.state_history_repo.save_transition(
                conversation_id=conversation.id,
                previous_state=previous_state,
                new_state=new_state,
                reason=reason,
            )
        return conversation

    def _polish_response(self, response: str, user_text: str, use_ai: bool = True) -> str:
        final_response = (response or "").strip()
        if use_ai:
            final_response = (
                self.ai.improve_response(
                    message=response,
                    last_user_message=user_text,
                )
                or response
                or ""
            ).strip()
        return self.responses.sanitize(final_response, user_text)

    # Delegaciones pequeñas conservan la API usada por pruebas y extensiones.
    def _component_responses(self) -> ConversationResponseBuilder:
        if not hasattr(self, "responses"):
            self.responses = ConversationResponseBuilder()
        return self.responses

    def _component_input(self) -> ConversationInputExtractor:
        if not hasattr(self, "input_extractor"):
            self.state_service = getattr(self, "state_service", ConversationStateService())
            self.credit_service = getattr(self, "credit_service", CreditApplicationService())
            self.input_extractor = ConversationInputExtractor(
                self.state_service,
                self.credit_service,
            )
        return self.input_extractor

    def _question_for_field(self, field: str, customer, application) -> str:
        return self._component_responses().question_for_field(field, customer, application)

    def _build_result_response(self, evaluation: dict, customer, application) -> str:
        return self._component_responses().build_result_response(
            evaluation,
            customer,
            application,
        )

    def _build_already_registered_response(self, customer, application) -> str:
        return self._component_responses().build_already_registered_response(
            customer,
            application,
        )

    def _profile_snapshot(self, customer, application) -> str:
        return self._component_responses().profile_snapshot(customer, application)

    def _human_result_label(self, result: str | None) -> str:
        return self._component_responses().human_result_label(result)

    def _human_join(self, items: list[str]) -> str:
        return self._component_responses().human_join(items)

    def _sanitize_response(self, response: str, user_text: str) -> str:
        return self._component_responses().sanitize(response, user_text)

    def _format_currency(self, value) -> str:
        return self._component_responses().format_currency(value)

    def _is_handoff_requested(self, text: str, ai_data: dict) -> bool:
        return ConversationPolicy.is_handoff_requested(text, ai_data)

    def _should_send_welcome(self, conversation, customer, application, text, ai_data):
        return ConversationPolicy.should_send_welcome(
            conversation,
            customer,
            application,
            text,
            ai_data,
        )

    def _is_plain_greeting(self, text: str) -> bool:
        return ConversationPolicy.is_plain_greeting(text)

    def _build_welcome_response(self) -> str:
        return ConversationPolicy.welcome_response()

    def _answer_faq_if_applicable(self, text: str) -> str:
        return self.faq_service.answer(text)

    def _build_ai_history(self, conversation_id: int, limit: int = 8) -> list[dict]:
        return build_ai_history(self.message_repo, conversation_id, limit)

    def _enrich_extracted_data(
        self,
        conversation,
        customer,
        application,
        text: str,
        ai_data: dict,
    ) -> dict:
        return self._component_input().enrich(
            conversation,
            customer,
            application,
            text,
            ai_data,
        )

    def _expected_field(self, conversation, customer, application) -> str | None:
        return self._component_input().expected_field(conversation, customer, application)

    def _extract_national_id(self, text: str) -> str | None:
        return self._component_input().extract_national_id(text)

    def _extract_name(self, text: str) -> str | None:
        return self._component_input().extract_name(text)

    def _extract_decimal(self, text: str):
        return self._component_input().extract_decimal(text)

    def _extract_term_months(self, text: str) -> int | None:
        return self._component_input().extract_term_months(text)

    def _clear_invalid_customer_name(self, customer) -> None:
        self._component_input().clear_invalid_customer_name(customer)
