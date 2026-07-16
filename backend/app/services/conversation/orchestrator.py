from sqlalchemy.orm import Session

from app.config.settings import settings
from app.repositories.ai_analysis_repository import AIAnalysisRepository
from app.repositories.conversation_context_repository import ConversationContextRepository
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.conversation_state_history_repository import (
    ConversationStateHistoryRepository,
)
from app.repositories.credit_application_repository import CreditApplicationRepository
from app.repositories.customer_repository import CustomerRepository
from app.repositories.message_repository import MessageRepository
from app.services.ai.ai_orchestrator import AIOrchestrator
from app.services.conversation.adaptive_flow import AdaptiveCreditFlow
from app.services.conversation.conversation_state_service import ConversationStateService
from app.services.conversation.credit_application_service import CreditApplicationService
from app.services.conversation.credit_prequalification_service import (
    CreditPrequalificationService,
)
from app.services.conversation.faq_answer_service import FAQAnswerService
from app.services.conversation.history import build_ai_history
from app.services.conversation.input_extractor import ConversationInputExtractor
from app.services.conversation.policy import ConversationPolicy
from app.services.conversation.response_builder import ConversationResponseBuilder
from app.services.conversation.slot_service import ConversationSlotService
from app.services.whatsapp.templates import (
    TransactionalTemplateKey,
    render_transactional_template,
)
from app.state_machine.states import ConversationState
from app.state_machine.transitions import can_transition


class ConversationOrchestrator:
    """Coordina un mensaje; delega extracción, políticas y presentación."""

    def __init__(self, db: Session):
        self.db = db
        self.customer_repo = CustomerRepository(db)
        self.conversation_repo = ConversationRepository(db)
        self.context_repo = ConversationContextRepository(db)
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
        self.slots = ConversationSlotService()
        self.adaptive_flow = AdaptiveCreditFlow(db, self.slots)
        self.prequalification = CreditPrequalificationService(db, self.slots)
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
        context = self.context_repo.get_or_create(conversation.id)
        application = self.application_repo.get_or_create_latest(customer.id)
        self.input_extractor.clear_invalid_customer_name(customer)
        self._clear_invalid_context_name(context, customer)
        self._save_message(conversation.id, "INBOUND", text, inbound_message_type)

        if settings.AI_ONLY_MODE:
            return self._answer_with_ai(conversation.id, text)
        if conversation.status == "HANDOFF":
            return ""
        if ConversationPolicy.is_handoff_requested(text, {}):
            self._handoff(conversation)
            return self._save_outbound(
                conversation.id,
                render_transactional_template(TransactionalTemplateKey.HANDOFF_REQUESTED),
            )

        self.adaptive_flow.handle_pending_consent(
            context,
            customer,
            conversation,
            text,
        )
        privacy_status = self.slots.status(context, "privacy_consent")
        if privacy_status == "DECLINED":
            faq_response = self.faq_service.answer(text)
            response = faq_response or (
                "Entendido. No continuare la precalificacion ni usare datos adicionales. "
                "Puedo darte informacion general sobre productos o derivarte con un asesor."
            )
            return self._save_outbound(conversation.id, response)
        if privacy_status != "GRANTED":
            if ConversationPolicy.is_plain_greeting(text):
                return self._save_outbound(
                    conversation.id,
                    ConversationPolicy.welcome_response(),
                )
            faq_response = self.faq_service.answer(text)
            if faq_response:
                return self._save_outbound(conversation.id, faq_response)
            context.pending_field = "privacy_consent"
            self._change_state(
                conversation,
                ConversationState.ASK_PRIVACY_CONSENT.value,
                "Se requiere informar y registrar el consentimiento de privacidad",
            )
            return self._save_outbound(
                conversation.id,
                self.adaptive_flow.privacy_question(),
            )

        name_confirmation = self.adaptive_flow.handle_pending_name_confirmation(
            context,
            customer,
            text,
        )
        if name_confirmation == "REJECTED":
            self._change_state(
                conversation,
                ConversationState.ASK_NAME.value,
                "El usuario rechazo el nombre sugerido",
            )
            return self._save_outbound(
                conversation.id,
                self.responses.name_correction_question(),
            )

        ai_data = self.input_extractor.enrich(
            conversation,
            customer,
            application,
            text,
            self.ai.analyze_message(text),
        )
        ai_data = self.input_extractor.enrich_pending_field(
            text,
            context.pending_field,
            ai_data,
        )
        self.ai_analysis_repo.save_analysis(
            conversation_id=conversation.id,
            intent=ai_data.get("intent"),
            extracted_data=ai_data,
            model_used=self.ai.get_model_name(),
        )

        if self.input_extractor.is_name_denial(text) and not ai_data.get("full_name"):
            self.slots.reject_slot(context, "full_name")
            customer.full_name = None
            context.pending_field = "full_name"
            self._change_state(
                conversation,
                ConversationState.ASK_NAME.value,
                "El usuario corrigio el nombre registrado",
            )
            return self._save_outbound(
                conversation.id,
                self.responses.name_correction_question(),
            )

        if ConversationPolicy.is_handoff_requested(text, ai_data):
            self._handoff(conversation)
            return self._save_outbound(
                conversation.id,
                render_transactional_template(TransactionalTemplateKey.HANDOFF_REQUESTED),
            )
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
        before_slots = self.slots.snapshot(context)
        self.adaptive_flow.apply_entities(
            context,
            customer,
            application,
            ai_data,
        )
        if context.pending_field and self.slots.status(context, context.pending_field) in {
            "CONFIRMED",
            "VERIFIED",
            "GRANTED",
            "DECLINED",
        }:
            context.pending_field = None
        bureau_profile = self.adaptive_flow.hydrate_from_bureau(context, customer)
        self.adaptive_flow.apply_entities(context, customer, application, {})
        slots_changed = before_slots != self.slots.snapshot(context)

        side_answer = ""
        if ai_data.get("intent") == "consulta":
            side_answer = self._generate_ai_response(
                conversation.id,
                text,
                allow_credit_bureau=self.slots.status(context, "bureau_consent") == "GRANTED",
            )
        if not side_answer:
            side_answer = self.faq_service.answer(text)

        return self._continue_credit_flow(
            conversation,
            context,
            customer,
            application,
            text,
            bureau_profile,
            side_answer,
            slots_changed,
        )

    def _continue_credit_flow(
        self,
        conversation,
        context,
        customer,
        application,
        text: str,
        bureau_profile: dict | None,
        side_answer: str = "",
        slots_changed: bool = False,
    ) -> str:
        if self.slots.status(context, "full_name") == "PROPOSED":
            context.pending_field = "full_name"
            self._change_state(
                conversation,
                ConversationState.ASK_NAME.value,
                "Se requiere confirmar el nombre sugerido",
            )
            question = self.responses.question_for_field(
                "full_name",
                customer,
                application,
                suggested_value=self.slots.value(context, "full_name"),
            )
            return self._save_outbound(
                conversation.id,
                self._join_answer_and_question(side_answer, question),
            )

        conflicts = self.slots.conflicts(context)
        if conflicts:
            field, slot = next(iter(conflicts.items()))
            context.pending_field = field
            question = self._conflict_question(field, slot)
            return self._save_outbound(
                conversation.id,
                self._join_answer_and_question(side_answer, question),
            )

        missing_field = self.slots.next_required_field(context)
        if missing_field:
            context.pending_field = missing_field
            question = (
                self.adaptive_flow.bureau_question()
                if missing_field == "bureau_consent"
                else self.responses.question_for_field(
                    missing_field,
                    customer,
                    application,
                    suggested_value=(
                        self.slots.value(context, "full_name")
                        if missing_field == "full_name"
                        and self.slots.status(context, "full_name") == "PROPOSED"
                        else None
                    ),
                )
            )
            self._change_state(
                conversation,
                self.state_service.state_for_missing_field(missing_field),
                f"Falta el campo conversacional: {missing_field}",
            )
            return self._save_outbound(
                conversation.id,
                self._join_answer_and_question(side_answer, question),
            )

        if (
            conversation.current_state == ConversationState.SHOW_RESULT.value
            and application.result
            and not slots_changed
        ):
            response = self._post_result_response(
                text,
                customer,
                application,
                side_answer,
            )
            return self._save_outbound(conversation.id, response)

        evaluation = self.prequalification.evaluate(context, application, bureau_profile)
        if evaluation:
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
                self._join_answer_and_question(side_answer, response),
            )

        response = self.responses.build_already_registered_response(customer, application)
        return self._save_outbound(conversation.id, response)

    def _post_result_response(
        self,
        text: str,
        customer,
        application,
        side_answer: str = "",
    ) -> str:
        if ConversationPolicy.is_result_explanation_requested(text):
            return self.responses.build_result_explanation_response(application)
        if ConversationPolicy.is_plain_greeting(text):
            return self.responses.build_post_result_help_response(application)
        fallback = self.responses.build_already_registered_response(customer, application)
        return self._join_answer_and_question(side_answer, fallback)

    @staticmethod
    def _join_answer_and_question(answer: str, question: str) -> str:
        parts = [part.strip() for part in (answer, question) if (part or "").strip()]
        return "\n\n".join(parts)

    @staticmethod
    def _conflict_question(field: str, slot: dict) -> str:
        labels = {
            "full_name": "nombre",
            "age": "edad",
            "employment_status": "situacion laboral",
            "employment_tenure": "antiguedad",
            "monthly_income": "ingreso mensual",
            "monthly_expenses": "gastos mensuales",
            "existing_debt_payments": "cuotas de deuda",
            "pep_status": "condicion PEP",
        }
        return (
            f"Tengo dos valores distintos para {labels.get(field, field)}: me indicaste "
            f"{slot.get('value')} y la fuente simulada registra {slot.get('external_value')}. "
            "¿Cual debo usar para esta simulacion?"
        )

    def _answer_with_ai(self, conversation_id: int, text: str) -> str:
        response = self._generate_ai_response(conversation_id, text)
        return self._save_outbound(conversation_id, response)

    def _generate_ai_response(
        self,
        conversation_id: int,
        text: str,
        allow_credit_bureau: bool = False,
    ) -> str:
        history = build_ai_history(self.message_repo, conversation_id)
        if history and history[-1].get("role") == "user":
            history = history[:-1]
        return self.ai.generate_whatsapp_reply(
            text=text,
            history=history,
            db=self.db,
            allow_credit_bureau=allow_credit_bureau,
        )

    def _handoff(self, conversation) -> None:
        self._change_state(
            conversation,
            ConversationState.HANDOFF.value,
            "Usuario solicito hablar con asesor humano",
        )
        conversation.status = "HANDOFF"
        self.db.flush()

    def _clear_invalid_context_name(self, context, customer) -> None:
        slot_name = self.slots.value(context, "full_name")
        if slot_name and not self.credit_service.is_valid_person_name(str(slot_name)):
            self.slots.reject_slot(context, "full_name", source="SYSTEM_VALIDATION")
            customer.full_name = None

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
