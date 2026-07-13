from app.database.base import Base
from app.database.session import engine
from sqlalchemy import inspect, text
from app.models import (
    AIAnalysis,
    Conversation,
    ConversationStateHistory,
    CreditApplication,
    Customer,
    KnowledgeBase,
    Message,
)


def init_db():
    Base.metadata.create_all(bind=engine)
    _ensure_conversation_response_mode()


def _ensure_conversation_response_mode():
    inspector = inspect(engine)
    columns = {column["name"] for column in inspector.get_columns("conversations")}

    if "response_mode" in columns:
        return

    with engine.begin() as connection:
        if engine.dialect.name == "sqlite":
            connection.execute(
                text("ALTER TABLE conversations ADD COLUMN response_mode VARCHAR(20) NOT NULL DEFAULT 'TEXT'")
            )
            return

        connection.execute(
            text("ALTER TABLE conversations ADD COLUMN response_mode VARCHAR(20) NOT NULL DEFAULT 'TEXT'")
        )
