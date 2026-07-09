from sqlalchemy.orm import Session
from app.models.conversation import Conversation


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

    def get_or_create_active(self, customer_id: int):
        conversation = self.get_open_by_customer(customer_id)

        if conversation:
            return conversation

        conversation = Conversation(
            customer_id=customer_id,
            current_state="START",
            status="ACTIVE"
        )

        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)

        return conversation

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