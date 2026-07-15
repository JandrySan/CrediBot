from app.database.base import Base
from app.database.session import engine
from app.models import (  # noqa: F401 - registra metadata de SQLAlchemy
    AIAnalysis,
    Conversation,
    ConversationStateHistory,
    CreditApplication,
    Customer,
    KnowledgeBase,
    Message,
)


def init_db() -> None:
    """Creación rápida reservada para pruebas y bases efímeras."""
    Base.metadata.create_all(bind=engine)
