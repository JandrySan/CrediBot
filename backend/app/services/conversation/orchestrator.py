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
from app.services.rag.retrieval_service import RetrievalService
from app.state_machine.states import ConversationState
from app.state_machine.transitions import can_transition


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

            response = self.ai.generate_whatsapp_reply(
                text=text,
                history=history,
                db=self.db,
            )
            self._save_message(conversation.id, "OUTBOUND", response, "TEXT")
            return response

        if conversation.status == "HANDOFF":
            # In handoff mode only the advisor should reply.
            return ""

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
            self._handoff(conversation)
            return ""

        if ai_data.get("intent") == "consulta":
            history = self._build_ai_history(conversation.id)
            if history and history[-1].get("role") == "user":
                history = history[:-1]

            response = self.ai.generate_whatsapp_reply(
                text=text,
                history=history,
                db=self.db,
            )
            if response:
                self._save_message(conversation.id, "OUTBOUND", response, "TEXT")
                return response

        faq_response = self._answer_faq_if_applicable(text)
        if faq_response:
            self._save_message(conversation.id, "OUTBOUND", faq_response, "TEXT")
            return faq_response

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

            response = self._build_result_response(evaluation, customer, application)
            response = self._polish_response(response, user_text=text, use_ai=True)
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

            response = self._question_for_field(missing_field, customer, application)
            response = self._polish_response(response, user_text=text, use_ai=False)
            self._save_message(conversation.id, "OUTBOUND", response, "TEXT")
            return response

        response = self._build_already_registered_response(customer, application)
        response = self._polish_response(response, user_text=text, use_ai=True)
        self._save_message(conversation.id, "OUTBOUND", response, "TEXT")
        return response

    def _question_for_field(self, field: str, customer, application) -> str:
        if field == "full_name":
            return (
                "Hola, que gusto saludarte. Soy CrediBot y te ayudare con tu precalificacion de credito. "
                "Para comenzar, me compartes tu nombre completo?"
            )

        if field == "amount":
            if customer.full_name:
                return (
                    f"Es un gusto hablar contigo, {customer.full_name}. "
                    "Para continuar con tu precalificacion, que monto deseas solicitar en dolares?"
                )

            return "Perfecto, para avanzar dime que monto deseas solicitar en dolares."

        if field == "term_months":
            if application.amount is not None:
                return (
                    f"Excelente, ya tengo registrado un monto de {self._format_currency(application.amount)}. "
                    "Ahora cuentame en cuantos meses te gustaria pagarlo."
                )

            return "Perfecto, en cuantos meses te gustaria pagar el credito?"

        if field == "monthly_income":
            details = []
            if application.amount is not None:
                details.append(f"un monto de {self._format_currency(application.amount)}")
            if application.term_months is not None:
                details.append(f"un plazo de {application.term_months} meses")

            if details:
                detail_text = self._human_join(details)
                return (
                    f"Super, ya tengo {detail_text}. "
                    "Para cerrar tu precalificacion, cual es tu ingreso mensual aproximado en dolares?"
                )

            return "Gracias. Para cerrar tu precalificacion, cual es tu ingreso mensual aproximado en dolares?"

        return "Cuentame un poco mas para poder ayudarte mejor con tu solicitud."

    def _build_result_response(self, evaluation: dict, customer, application) -> str:
        profile_details = self._profile_snapshot(customer, application)
        result_label = self._human_result_label(evaluation.get("result"))
        reason = (evaluation.get("reason") or "").strip()

        if profile_details:
            return (
                f"Listo, con la informacion que me compartiste ({profile_details}), "
                f"tu resultado preliminar es {result_label}. "
                f"Motivo: {reason}. "
                "Si deseas, tambien puedo derivarte con un asesor humano."
            )

        return (
            f"Listo, tu resultado preliminar es {result_label}. "
            f"Motivo: {reason}. "
            "Si deseas, tambien puedo derivarte con un asesor humano."
        )

    def _handoff(self, conversation):
        self._change_state(
            conversation=conversation,
            new_state=ConversationState.HANDOFF.value,
            reason="Usuario solicito hablar con asesor humano",
        )

        conversation.status = "HANDOFF"
        self.db.commit()

    def _is_handoff_requested(self, text: str, ai_data: dict) -> bool:
        if ai_data.get("intent") == "asesor":
            return True

        normalized = text.lower()
        return any(
            word in normalized
            for word in ["asesor", "humano", "persona", "agente", "ejecutivo"]
        )

    def _answer_faq_if_applicable(self, text: str) -> str:
        normalized = (text or "").lower().strip()
        if not normalized:
            return ""

        question_markers = [
            "?",
            "¿",
            "requisito",
            "documento",
            "politica",
            "política",
            "tasa",
            "interes",
            "interés",
            "condicion",
            "condición",
            "plazo maximo",
            "plazo máximo",
            "pago anticipado",
        ]

        if not any(marker in normalized for marker in question_markers):
            return ""

        faq = RetrievalService(self.db).best_match(text)
        if not faq:
            return ""

        base_response = (
            f"{faq.answer} "
            "Si quieres, tambien puedo ayudarte con tu precalificacion de credito."
        )
        faq_context = f"Pregunta: {faq.question}\nRespuesta: {faq.answer}"
        return self.ai.response_generator.generate(
            base_message=base_response,
            last_user_message=text,
            faq_context=faq_context,
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
        current = conversation.current_state

        if current != new_state and not can_transition(current, new_state):
            allowed = self.state_service.get_allowed_transition_names(current)
            raise ValueError(
                f"Transicion invalida: {current} -> {new_state}. "
                f"Transiciones permitidas: {allowed}"
            )

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

    def _build_already_registered_response(self, customer, application) -> str:
        profile_details = self._profile_snapshot(customer, application)
        if profile_details:
            return (
                f"Tu solicitud ya fue registrada con estos datos: {profile_details}. "
                "Si quieres continuar o ajustar algo, lo revisamos juntos. "
                "Tambien puedes escribir asesor para hablar con una persona."
            )

        return (
            "Tu solicitud ya fue registrada. "
            "Si quieres, tambien puedo derivarte con un asesor humano."
        )

    def _profile_snapshot(self, customer, application) -> str:
        details: list[str] = []

        if customer.full_name:
            details.append(f"nombre {customer.full_name}")

        if application.amount is not None:
            details.append(f"monto de {self._format_currency(application.amount)}")

        if application.term_months is not None:
            details.append(f"plazo de {application.term_months} meses")

        if application.monthly_income is not None:
            details.append(f"ingresos mensuales de {self._format_currency(application.monthly_income)}")

        return self._human_join(details)

    def _human_result_label(self, result: str | None) -> str:
        normalized = (result or "").strip().upper()
        labels = {
            "PREAPROBADO": "preaprobado",
            "OBSERVADO": "observado",
            "RECHAZADO": "rechazado",
        }

        if normalized in labels:
            return labels[normalized]

        return normalized.lower() if normalized else "sin resultado"

    def _human_join(self, items: list[str]) -> str:
        clean_items = [item.strip() for item in items if (item or "").strip()]
        if not clean_items:
            return ""

        if len(clean_items) == 1:
            return clean_items[0]

        if len(clean_items) == 2:
            return f"{clean_items[0]} y {clean_items[1]}"

        return f"{', '.join(clean_items[:-1])} y {clean_items[-1]}"

    def _polish_response(self, response: str, user_text: str, use_ai: bool = True) -> str:
        final_response = (response or "").strip()

        if use_ai:
            improved = self.ai.improve_response(
                message=response,
                last_user_message=user_text,
            )
            final_response = (improved or response or "").strip()

        return self._sanitize_response(final_response, user_text=user_text)

    def _sanitize_response(self, response: str, user_text: str) -> str:
        cleaned = (response or "").strip()
        if not cleaned:
            return cleaned

        normalized_user = (user_text or "").lower()
        user_thanked = any(
            token in normalized_user
            for token in ["gracias", "agradezco", "thank you", "thanks"]
        )

        if not user_thanked:
            cleaned = re.sub(
                r"^\s*(de nada|no hay de que|con gusto|a la orden|encantado de ayudarte|un gusto ayudarte)[\s,:\-\.!]*",
                "",
                cleaned,
                flags=re.IGNORECASE,
            ).strip()

        cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

        return cleaned.strip()

    def _format_currency(self, value) -> str:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return str(value)

        formatted = f"{number:,.2f}"
        return f"${formatted}"
