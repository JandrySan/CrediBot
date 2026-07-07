from sqlalchemy.orm import Session
from app.models.conversation import Conversation


class ConversationRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_active_by_customer(self, customer_id: int):
        return (
            self.db.query(Conversation)
            .filter(
                Conversation.customer_id == customer_id,
                Conversation.status == "ACTIVE"
            )
            .first()
        )

    def get_or_create_active(self, customer_id: int):
        conversation = self.get_active_by_customer(customer_id)

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