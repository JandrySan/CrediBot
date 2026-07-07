from app.database.base import Base
from app.database.session import engine

from app.models import Customer, Conversation, Message, CreditApplication


def init_db():
    Base.metadata.create_all(bind=engine)