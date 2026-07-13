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
    _ensure_customer_national_id()
    _ensure_credit_application_reason_text()
    _ensure_conversation_response_mode()


def _ensure_customer_national_id():
    inspector = inspect(engine)
    columns = {column["name"] for column in inspector.get_columns("customers")}

    with engine.begin() as connection:
        if "national_id" not in columns:
            connection.execute(
                text("ALTER TABLE customers ADD COLUMN national_id VARCHAR(10)")
            )

        connection.execute(
            text("CREATE INDEX IF NOT EXISTS idx_customers_national_id ON customers(national_id)")
        )


def _ensure_credit_application_reason_text():
    if engine.dialect.name == "sqlite":
        return

    inspector = inspect(engine)
    columns = {
        column["name"]: column
        for column in inspector.get_columns("credit_applications")
    }
    reason_column = columns.get("reason")

    if not reason_column:
        return

    if "TEXT" in str(reason_column.get("type", "")).upper():
        return

    with engine.begin() as connection:
        connection.execute(
            text("ALTER TABLE credit_applications ALTER COLUMN reason TYPE TEXT")
        )


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
