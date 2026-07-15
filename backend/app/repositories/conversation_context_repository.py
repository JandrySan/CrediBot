from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.conversation_context import ConversationContext


class ConversationContextRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_or_create(self, conversation_id: int) -> ConversationContext:
        context = self.db.scalar(
            select(ConversationContext).where(
                ConversationContext.conversation_id == conversation_id
            )
        )
        if context:
            return context

        context = ConversationContext(conversation_id=conversation_id, slots={})
        self.db.add(context)
        self.db.flush()
        self.db.refresh(context)
        return context

    def save(self, context: ConversationContext) -> ConversationContext:
        self.db.add(context)
        self.db.flush()
        return context
