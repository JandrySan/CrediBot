from sqlalchemy.orm import Session

from app.config.settings import settings
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.customer_repository import CustomerRepository


class ConversationSessionService:
    """Administra expiración y limpieza; no procesa mensajes del cliente."""

    def __init__(self, db: Session, session_timeout_minutes: int | None = None):
        self.db = db
        self.session_timeout_minutes = (
            settings.CONVERSATION_SESSION_TIMEOUT_MINUTES
            if session_timeout_minutes is None
            else session_timeout_minutes
        )
        self.customer_repo = CustomerRepository(db)
        self.conversation_repo = ConversationRepository(db)

    def restore_session(self, phone_number: str):
        customer = self.customer_repo.get_by_phone(phone_number)
        if not customer:
            return None

        conversation = self.conversation_repo.restore_session(
            customer_id=customer.id,
            timeout_minutes=self.session_timeout_minutes,
        )
        return conversation

    def cleanup_sessions(self) -> dict[str, int]:
        closed_count = self.conversation_repo.cleanup_expired_open_sessions(
            timeout_minutes=self.session_timeout_minutes,
            limit=settings.CONVERSATION_CLEANUP_BATCH_SIZE,
        )
        empty_deleted = self.conversation_repo.purge_empty_closed_sessions(
            limit=settings.CONVERSATION_CLEANUP_BATCH_SIZE,
        )
        abandoned_deleted = self.conversation_repo.purge_abandoned_closed_sessions(
            retention_days=settings.ABANDONED_CONVERSATION_RETENTION_DAYS,
            limit=settings.CONVERSATION_CLEANUP_BATCH_SIZE,
        )
        return {
            "closed_count": closed_count,
            "deleted_count": empty_deleted + abandoned_deleted,
        }
