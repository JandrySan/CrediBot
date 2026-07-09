from decimal import Decimal, InvalidOperation
import re

from sqlalchemy.orm import Session

from app.config.settings import settings
from app.repositories.ai_analysis_repository import AIAnalysisRepository
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.conversation_state_history_repository import ConversationStateHistoryRepository
from app.repositories.credit_application_repository import CreditApplicationRepository
from app.repositories.customer_repository import CustomerRepository
from app.repositories.message_repository import MessageRepository
from app.services.ai.ai_orchestrator import AIOrchestrator
from app.services.conversation.conversation_state_service import ConversationStateService
from app.services.conversation.credit_application_service import CreditApplicationService
from app.state_machine.states import ConversationState


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

    def handle_text_message(self, phone_number: str, text: str) -> str:
        return self._handle_message(
            phone_number=phone_number,
            text=text,
            inbound_message_type="TEXT",
        )

    def handle_audio_message(self, phone_number: str, transcript_text: str) -> str:
        return self._handle_message(
            phone_number=phone_number,
            text=transcript_text,
            inbound_message_type="AUDIO",
        )

    def _handle_message(
        self,
        phone_number: str,
        text: str,
        inbound_message_type: str = "TEXT",
    ) -> str:
        text = (text or "").strip()

        customer = self.customer_repo.get_or_create(phone_number)
        conversation = self.conversation_repo.get_or_create_active(customer.id)
        application = self.application_repo.get_or_create_latest(customer.id)

        self._save_message(
            conversation_id=conversation.id,
            direction="INBOUND",
            content=text,
            message_type=inbound_message_type,
        )

        if settings.AI_ONLY_MODE:
            history = self._build_ai_history(conversation.id)
            if history and history[-1].get("role") == "user":
                history = history[:-1]

            response = self.ai.generate_whatsapp_reply(text=text, history=history)
            self._save_message(conversation.id, "OUTBOUND", response, "TEXT")
            return response

        if conversation.status == "HANDOFF":
            response = "Tu mensaje fue recibido. Un asesor humano te respondera en breve."
            self._save_message(conversation.id, "OUTBOUND", response, "TEXT")
            return response

        ai_data = self.ai.analyze_message(text)
        ai_data = self._enrich_extracted_data(
            conversation=conversation,
            customer=customer,
            application=application,
            text=text,
            ai_data=ai_data,
        )

        self.ai_analysis_repo.save_analysis(
            conversation_id=conversation.id,
            intent=ai_data.get("intent"),
            extracted_data=ai_data,
            model_used=self.ai.get_model_name(),
        )

        if self._is_handoff_requested(text, ai_data):
            response = self._handoff(conversation)
            self._save_message(conversation.id, "OUTBOUND", response, "TEXT")
            return response

        self.credit_service.apply_extracted_data(
            customer=customer,
            application=application,
            data=ai_data,
            db=self.db,
        )

        evaluation = self.credit_service.evaluate_if_complete(application)

        if evaluation:
            self.application_repo.update(
                application,
                result=evaluation["result"],
                reason=evaluation["reason"],
            )

            conversation.result = evaluation["result"]
            self.db.commit()

            self._change_state(
                conversation=conversation,
                new_state=ConversationState.SHOW_RESULT.value,
                reason="Solicitud completa y evaluada",
            )

            response = self._build_result_response(evaluation)
            response = self.ai.improve_response(response)
            response = self._with_user_data_summary(response, customer, application)
            self._save_message(conversation.id, "OUTBOUND", response, "TEXT")
            return response

        missing_field = self.state_service.get_next_required_field(customer, application)

        if missing_field:
            new_state = self.state_service.state_for_missing_field(missing_field)

            self._change_state(
                conversation=conversation,
                new_state=new_state,
                reason=f"Falta el campo requerido: {missing_field}",
            )

            response = self._question_for_field(missing_field, customer)
            response = self.ai.improve_response(response)
            response = self._with_user_data_summary(response, customer, application)
            self._save_message(conversation.id, "OUTBOUND", response, "TEXT")
            return response

        response = (
            "Tu solicitud ya fue registrada. "
            "Puedes escribir asesor si deseas hablar con una persona."
        )
        response = self._with_user_data_summary(response, customer, application)
        self._save_message(conversation.id, "OUTBOUND", response, "TEXT")
        return response

    def _question_for_field(self, field: str, customer) -> str:
        questions = {
            "full_name": (
                "Hola. Soy CrediBot. "
                "Te ayudare con una precalificacion rapida de credito. "
                "Para empezar, dime tu nombre completo."
            ),
            "amount": (
                f"Mucho gusto, {customer.full_name}. "
                "Que monto deseas solicitar? Escribe el valor en dolares."
            ),
            "term_months": "Perfecto. En cuantos meses deseas pagar el credito?",
            "monthly_income": "Gracias. Ahora dime tus ingresos mensuales aproximados en dolares.",
        }

        return questions[field]

    def _build_result_response(self, evaluation: dict) -> str:
        return (
            f"Resultado de precalificacion: {evaluation['result']}.\n\n"
            f"Motivo: {evaluation['reason']}\n\n"
            "Este resultado es preliminar. "
            "Puedes escribir asesor en cualquier momento para hablar con una persona."
        )

    def _handoff(self, conversation) -> str:
        self._change_state(
            conversation=conversation,
            new_state=ConversationState.HANDOFF.value,
            reason="Usuario solicito hablar con asesor humano",
        )

        conversation.status = "HANDOFF"
        self.db.commit()

        return "Entendido. Te voy a derivar con un asesor humano. Por favor espera un momento."

    def _is_handoff_requested(self, text: str, ai_data: dict) -> bool:
        if ai_data.get("intent") == "asesor":
            return True

        normalized = text.lower()
        return any(
            word in normalized
            for word in ["asesor", "humano", "persona", "agente", "ejecutivo"]
        )

    def _save_message(
        self,
        conversation_id: int,
        direction: str,
        content: str,
        message_type: str = "TEXT",
    ):
        self.message_repo.save_message(
            conversation_id=conversation_id,
            direction=direction,
            content=content,
            message_type=message_type,
        )

    def _change_state(self, conversation, new_state: str, reason: str):
        conversation, previous_state, changed = self.conversation_repo.update_state_if_changed(
            conversation,
            new_state,
        )

        if changed:
            self.state_history_repo.save_transition(
                conversation_id=conversation.id,
                previous_state=previous_state,
                new_state=new_state,
                reason=reason,
            )

        return conversation

    def _build_ai_history(self, conversation_id: int, limit: int = 8) -> list[dict]:
        rows = self.message_repo.get_recent_messages(
            conversation_id=conversation_id,
            limit=limit,
        )
        history: list[dict] = []

        for row in reversed(rows):
            role = "assistant" if row.direction == "OUTBOUND" else "user"
            content = (row.content or "").strip()

            if content:
                history.append({"role": role, "content": content})

        return history

    def _enrich_extracted_data(
        self,
        conversation,
        customer,
        application,
        text: str,
        ai_data: dict,
    ) -> dict:
        enriched = dict(ai_data or {})

        expected_field = self._expected_field(conversation, customer, application)
        if not expected_field:
            return enriched

        if enriched.get(expected_field):
            return enriched

        if expected_field == "full_name":
            fallback_name = self._extract_name(text)
            if fallback_name:
                enriched["full_name"] = fallback_name
            return enriched

        if expected_field == "term_months":
            fallback_term = self._extract_term_months(text)
            if fallback_term is not None:
                enriched["term_months"] = fallback_term
            return enriched

        if expected_field in {"amount", "monthly_income"}:
            fallback_amount = self._extract_decimal(text)
            if fallback_amount is not None:
                enriched[expected_field] = str(fallback_amount)

        return enriched

    def _expected_field(self, conversation, customer, application) -> str | None:
        by_state = {
            ConversationState.ASK_NAME.value: "full_name",
            ConversationState.ASK_AMOUNT.value: "amount",
            ConversationState.ASK_TERM.value: "term_months",
            ConversationState.ASK_INCOME.value: "monthly_income",
        }

        state_field = by_state.get(conversation.current_state)
        if state_field:
            return state_field

        return self.state_service.get_next_required_field(customer, application)

    def _extract_name(self, text: str) -> str | None:
        value = (text or "").strip()
        if not value:
            return None

        if re.search(r"\d", value):
            return None

        cleaned = re.sub(r"[^A-Za-z\s]", " ", value)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()

        if len(cleaned) < 2:
            return None

        blacklist = {"hola", "buenas", "gracias", "ok", "credito"}
        if cleaned.lower() in blacklist:
            return None

        return cleaned[:120]

    def _extract_decimal(self, text: str):
        value = (text or "").strip()
        if not value:
            return None

        match = re.search(r"\d[\d\.,]*", value)
        if not match:
            return None

        raw = match.group(0)
        normalized = raw.replace(",", "").replace(" ", "")

        try:
            return Decimal(normalized)
        except InvalidOperation:
            return None

    def _extract_term_months(self, text: str) -> int | None:
        value = (text or "").lower().strip()
        if not value:
            return None

        match = re.search(r"\d+", value)
        if not match:
            return None

        number = int(match.group(0))
        if number <= 0:
            return None

        if any(token in value for token in ["ano", "anos", "year", "years"]):
            return number * 12

        return number

    def _with_user_data_summary(self, response: str, customer, application) -> str:
        summary_lines: list[str] = []

        if customer.full_name:
            summary_lines.append(f"- Nombre: {customer.full_name}")

        if application.amount is not None:
            summary_lines.append(f"- Monto solicitado: {self._format_currency(application.amount)}")

        if application.term_months is not None:
            summary_lines.append(f"- Plazo: {application.term_months} meses")

        if application.monthly_income is not None:
            summary_lines.append(f"- Ingresos mensuales: {self._format_currency(application.monthly_income)}")

        if not summary_lines:
            return response

        return (
            f"{response}\n\n"
            "Datos que registre hasta ahora:\n"
            f"{chr(10).join(summary_lines)}"
        )

    def _format_currency(self, value) -> str:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return str(value)

        formatted = f"{number:,.2f}"
        return f"${formatted}"
