from app.database.base import Base
from app.database.session import engine
from app.models import Customer, Conversation, Message, CreditApplication, AIAnalysis
from app.models import ConversationStateHistory, DocumentChunk


def init_db():
    Base.metadata.create_all(bind=engine)

    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()
    except Exception:
        pass
