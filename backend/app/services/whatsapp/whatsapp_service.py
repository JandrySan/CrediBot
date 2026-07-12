from sqlalchemy.orm import Session

from app.config.settings import settings
from app.services.conversation.orchestrator import ConversationOrchestrator
from app.services.ai.ai_orchestrator import AIOrchestrator


class WhatsAppService:
    def __init__(self, db: Session):
        self.db = db
        self.orchestrator = ConversationOrchestrator(db)
        self.ai_orchestrator = AIOrchestrator()

    def process_inbound_message(
        self,
        phone_number: str,
        text: str,
        message_type: str = "TEXT",
        profile_name: str = "",
    ) -> str:
        if settings.AI_ONLY_MODE:
            return self._handle_ai_only(phone_number, text, message_type)

        return self.orchestrator.handle_text_message(
            phone_number=phone_number,
            text=text,
        )

    def process_audio_transcript(
        self,
        phone_number: str,
        transcript_text: str,
        profile_name: str = "",
    ) -> str:
        return self.orchestrator.handle_audio_message(
            phone_number=phone_number,
            transcript_text=transcript_text,
        )

    def _handle_ai_only(
        self,
        phone_number: str,
        text: str,
        message_type: str = "TEXT",
    ) -> str:
        from app.repositories.conversation_repository import ConversationRepository
        from app.repositories.customer_repository import CustomerRepository
        from app.repositories.message_repository import MessageRepository

        customer_repo = CustomerRepository(self.db)
        conversation_repo = ConversationRepository(self.db)
        message_repo = MessageRepository(self.db)

        customer = customer_repo.get_or_create(phone_number)
        conversation = conversation_repo.get_or_create_active(customer.id)

        message_repo.save_message(
            conversation_id=conversation.id,
            direction="INBOUND",
            content=text,
            message_type=message_type,
        )

        history = self.orchestrator._build_ai_history(conversation.id)
        if history and history[-1].get("role") == "user":
            history = history[:-1]

        response = self.ai_orchestrator.generate_whatsapp_reply(
            text=text,
            history=history,
        )

        message_repo.save_message(
            conversation_id=conversation.id,
            direction="OUTBOUND",
            content=response,
            message_type="TEXT",
        )

        return response
