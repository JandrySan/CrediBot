from sqlalchemy.orm import Session
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
        self.db.commit()
        self.db.refresh(message)

        return message
    

    