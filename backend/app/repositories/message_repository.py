from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from app.models.conversation import Conversation
from app.models.message import Message


class MessageRepository:
    def __init__(self, db: Session):
        self.db = db

    def save_message(
        self,
        conversation_id: int,
        direction: str,
        content: str,
        message_type: str = "TEXT"
    ):
        message = Message(
            conversation_id=conversation_id,
            direction=direction,
            content=content,
            message_type=message_type
        )

        self.db.add(message)
        self.db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).update({Conversation.updated_at: func.now()})
        self.db.commit()
        self.db.refresh(message)

        return message

    def get_recent_messages(self, conversation_id: int, limit: int = 8):
        return (
            self.db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.id.desc())
            .limit(limit)
            .all()
        )
