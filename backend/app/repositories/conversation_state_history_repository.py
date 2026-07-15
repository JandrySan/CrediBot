from sqlalchemy.orm import Session

from app.models.conversation_state_history import ConversationStateHistory


class ConversationStateHistoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def save_transition(
        self,
        conversation_id: int,
        previous_state: str | None,
        new_state: str,
        reason: str | None = None,
    ):
        transition = ConversationStateHistory(
            conversation_id=conversation_id,
            previous_state=previous_state,
            new_state=new_state,
            reason=reason,
        )

        self.db.add(transition)
        self.db.flush()
        self.db.refresh(transition)

        return transition
