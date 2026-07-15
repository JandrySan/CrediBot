from typing import ClassVar

from sqlalchemy.orm import Session

from app.models.conversation import Conversation
from app.models.credit_application import CreditApplication
from app.models.customer import Customer
from app.models.message import Message
from app.services.conversation.session_service import ConversationSessionService
from app.services.whatsapp.twilio_service import TwilioWhatsAppService
from app.state_machine.states import ConversationState


class DashboardConversationService:
    RESOLUTIONS: ClassVar[dict[str, tuple[str, str]]] = {
        "APPROVED": ("APROBADO_ASESOR", "Credito aprobado por asesor"),
        "DENIED": ("NEGADO_ASESOR", "Credito negado por asesor"),
        "RESOLVED": ("RESUELTO_ASESOR", "Duda resuelta por asesor"),
    }

    def __init__(self, db: Session):
        self.db = db

    def cleanup(self) -> dict[str, int]:
        return ConversationSessionService(self.db).cleanup_sessions()

    def take(self, conversation_id: int) -> dict:
        conversation = self._conversation(conversation_id)
        error = self._take_validation_error(conversation)
        if error:
            return error
        assert conversation is not None

        customer = self.db.get(Customer, conversation.customer_id)
        conversation.status = "HANDOFF"
        conversation.current_state = ConversationState.HANDOFF.value
        conversation.response_mode = "TEXT"
        self.db.flush()

        twilio_result = {"success": False, "message": "Cliente no encontrado"}
        if customer:
            twilio_result = TwilioWhatsAppService().send_message(
                to=customer.phone_number,
                body=(
                    "Un asesor humano tomo tu conversacion. Desde ahora te "
                    "respondera directamente por este chat."
                ),
            )

        return {
            "success": True,
            "message": "Conversacion tomada por asesor",
            "conversation_id": conversation.id,
            "status": conversation.status,
            "state": conversation.current_state,
            "customer_notified": bool(twilio_result.get("success", False)),
            "twilio": twilio_result,
        }

    def reply(self, conversation_id: int, message: str) -> dict:
        conversation = self._conversation(conversation_id)
        error = self._reply_validation_error(conversation)
        if error:
            return error
        assert conversation is not None

        customer = self.db.get(Customer, conversation.customer_id)
        if not customer:
            return {"success": False, "message": "Cliente no encontrado"}

        twilio_result = TwilioWhatsAppService().send_message(
            to=customer.phone_number,
            body=message,
        )
        if not twilio_result.get("success", False):
            return {
                "success": False,
                "message": twilio_result.get(
                    "message",
                    "No se pudo enviar el mensaje por WhatsApp",
                ),
                "conversation_id": conversation.id,
                "message_saved": False,
                "whatsapp_sent": False,
                "twilio": twilio_result,
            }

        self.db.add(
            Message(
                conversation_id=conversation.id,
                direction="OUTBOUND",
                message_type="TEXT",
                content=message,
            )
        )
        self.db.flush()
        return {
            "success": True,
            "message": "Respuesta enviada por asesor",
            "conversation_id": conversation.id,
            "message_saved": True,
            "whatsapp_sent": True,
            "twilio": twilio_result,
        }

    def close(self, conversation_id: int, resolution: str, note: str) -> dict:
        conversation = self._conversation(conversation_id)
        if not conversation:
            return {"success": False, "message": "Conversacion no encontrada"}
        if conversation.status != "HANDOFF":
            return {
                "success": False,
                "message": "Solo puedes cerrar conversaciones en estado HANDOFF.",
            }

        normalized = (resolution or "").strip().upper()
        if normalized not in self.RESOLUTIONS:
            normalized = "RESOLVED"
        conversation_result, reason = self.RESOLUTIONS[normalized]
        application = self._latest_application(conversation.customer_id)
        self._resolve_application(application, normalized, reason, note)

        conversation.status = "CLOSED"
        conversation.current_state = ConversationState.END.value
        conversation.result = conversation_result
        self.db.flush()
        return {
            "success": True,
            "message": (
                "Conversacion cerrada. El siguiente mensaje del cliente iniciara "
                "un nuevo flujo con el bot."
            ),
            "conversation_id": conversation.id,
            "status": conversation.status,
            "state": conversation.current_state,
            "resolution": normalized,
        }

    def _conversation(self, conversation_id: int) -> Conversation | None:
        return self.db.get(Conversation, conversation_id)

    @staticmethod
    def _take_validation_error(conversation: Conversation | None) -> dict | None:
        if not conversation:
            return {"success": False, "message": "Conversacion no encontrada"}
        if conversation.status == "CLOSED":
            return {
                "success": False,
                "message": (
                    "La conversacion esta cerrada. Espera una nueva conversacion del cliente."
                ),
            }
        return None

    @staticmethod
    def _reply_validation_error(conversation: Conversation | None) -> dict | None:
        if not conversation:
            return {"success": False, "message": "Conversacion no encontrada"}
        if conversation.status != "HANDOFF":
            return {
                "success": False,
                "message": (
                    "Solo puedes responder manualmente cuando la conversacion esta en HANDOFF."
                ),
            }
        return None

    def _latest_application(self, customer_id: int) -> CreditApplication | None:
        return (
            self.db.query(CreditApplication)
            .filter(CreditApplication.customer_id == customer_id)
            .order_by(CreditApplication.id.desc())
            .first()
        )

    @staticmethod
    def _resolve_application(
        application: CreditApplication | None,
        resolution: str,
        reason: str,
        note: str,
    ) -> None:
        if not application or application.result is not None:
            return

        result_by_resolution = {
            "APPROVED": "PREAPROBADO",
            "DENIED": "OBSERVADO",
            "RESOLVED": "RESUELTO_ASESOR",
        }
        application.result = result_by_resolution[resolution]
        clean_note = (note or "").strip()
        application.reason = f"{reason}. Nota: {clean_note}" if clean_note else reason
