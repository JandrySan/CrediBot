from app.database.base import Base
from app.database.session import engine
from app.models import Customer, Conversation, Message, CreditApplication, AIAnalysis

from app.models import Customer, Conversation, Message, CreditApplication, AIAnalysis, ConversationStateHistory


def init_db():
    Base.metadata.create_all(bind=engine)