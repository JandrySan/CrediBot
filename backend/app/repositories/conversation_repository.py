from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.models.conversation import Conversation
from app.state_machine.states import ConversationState


OPEN_CONVERSATION_STATUSES = ("ACTIVE", "HANDOFF")


class ConversationRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_open_by_customer(self, customer_id: int):
        return (
            self.db.query(Conversation)
            .filter(
                Conversation.customer_id == customer_id,
                Conversation.status.in_(OPEN_CONVERSATION_STATUSES),
            )
            .order_by(Conversation.id.desc())
            .first()
        )

    def get_or_create_active(self, customer_id: int, timeout_minutes: int | None = None):
        conversation = self.get_open_by_customer(customer_id)

        if conversation:
            if self.is_expired(conversation, timeout_minutes=timeout_minutes):
                self.close_expired(conversation)
            else:
                return conversation

        return self.create_active(customer_id)

    def restore_session(self, customer_id: int, timeout_minutes: int | None = None):
        conversation = self.get_open_by_customer(customer_id)

        if not conversation:
            return None

        if self.is_expired(conversation, timeout_minutes=timeout_minutes):
            self.close_expired(conversation)
            return None

        return conversation

    def create_active(self, customer_id: int):
        conversation = Conversation(
            customer_id=customer_id,
            current_state=ConversationState.START.value,
            status="ACTIVE"
        )

        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)

        return conversation

    def is_expired(self, conversation: Conversation, timeout_minutes: int | None = None) -> bool:
        timeout = self._timeout_minutes(timeout_minutes)
        if timeout <= 0:
            return False

        last_activity = (
            getattr(conversation, "updated_at", None)
            or getattr(conversation, "created_at", None)
        )
        if not last_activity:
            return False

        if last_activity.tzinfo is None:
            last_activity = last_activity.replace(tzinfo=timezone.utc)

        expires_at = last_activity + timedelta(minutes=timeout)
        return datetime.now(timezone.utc) >= expires_at

    def close_expired(self, conversation: Conversation):
        conversation.status = "CLOSED"
        conversation.current_state = ConversationState.END.value
        conversation.result = conversation.result or "EXPIRADO"
        conversation.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(conversation)
        return conversation

    def cleanup_expired_open_sessions(self, timeout_minutes: int | None = None, limit: int | None = None) -> int:
        timeout = self._timeout_minutes(timeout_minutes)
        if timeout <= 0:
            return 0

        cutoff = datetime.now(timezone.utc) - timedelta(minutes=timeout)
        max_rows = limit or settings.CONVERSATION_CLEANUP_BATCH_SIZE

        conversations = (
            self.db.query(Conversation)
            .filter(
                Conversation.status.in_(OPEN_CONVERSATION_STATUSES),
                func.coalesce(Conversation.updated_at, Conversation.created_at) <= cutoff,
            )
            .order_by(Conversation.id.asc())
            .limit(max_rows)
            .all()
        )

        for conversation in conversations:
            conversation.status = "CLOSED"
            conversation.current_state = ConversationState.END.value
            conversation.result = conversation.result or "EXPIRADO"
            conversation.updated_at = datetime.now(timezone.utc)

        if conversations:
            self.db.commit()

        return len(conversations)

    def touch(self, conversation: Conversation):
        conversation.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(conversation)
        return conversation

    def _timeout_minutes(self, timeout_minutes: int | None = None) -> int:
        value = (
            settings.CONVERSATION_SESSION_TIMEOUT_MINUTES
            if timeout_minutes is None
            else timeout_minutes
        )

        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    def update_state(self, conversation: Conversation, new_state: str):
        conversation.current_state = new_state
        self.db.commit()
        self.db.refresh(conversation)

        return conversation
    
    def update_state_if_changed(self, conversation: Conversation, new_state: str):
        previous_state = conversation.current_state

        if previous_state == new_state:
            return conversation, previous_state, False

        conversation.current_state = new_state
        self.db.commit()
        self.db.refresh(conversation)

        return conversation, previous_state, True
