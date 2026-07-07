from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database.session import get_db
from app.models.customer import Customer
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.credit_application import CreditApplication

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    return {
        "customers": db.query(Customer).count(),
        "conversations": db.query(Conversation).count(),
        "active_conversations": db.query(Conversation).filter(
            Conversation.status == "ACTIVE"
        ).count(),
        "handoff_conversations": db.query(Conversation).filter(
            Conversation.status == "HANDOFF"
        ).count(),
        "preapproved": db.query(CreditApplication).filter(
            CreditApplication.result == "PREAPROBADO"
        ).count(),
        "observed": db.query(CreditApplication).filter(
            CreditApplication.result == "OBSERVADO"
        ).count(),
    }


@router.get("/conversations")
def get_conversations(db: Session = Depends(get_db)):
    conversations = (
        db.query(Conversation, Customer, CreditApplication)
        .join(Customer, Conversation.customer_id == Customer.id)
        .outerjoin(CreditApplication, CreditApplication.customer_id == Customer.id)
        .order_by(Conversation.id.desc())
        .all()
    )

    return [
        {
            "conversation_id": conversation.id,
            "customer_id": customer.id,
            "phone_number": customer.phone_number,
            "full_name": customer.full_name,
            "state": conversation.current_state,
            "status": conversation.status,
            "conversation_result": conversation.result,
            "credit_amount": float(application.amount) if application and application.amount else None,
            "term_months": application.term_months if application else None,
            "monthly_income": float(application.monthly_income) if application and application.monthly_income else None,
            "credit_result": application.result if application else None,
            "credit_reason": application.reason if application else None,
            "created_at": conversation.created_at,
        }
        for conversation, customer, application in conversations
    ]


@router.get("/conversations/{conversation_id}/messages")
def get_conversation_messages(
    conversation_id: int,
    db: Session = Depends(get_db)
):
    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.id.asc())
        .all()
    )

    return [
        {
            "id": message.id,
            "direction": message.direction,
            "type": message.message_type,
            "content": message.content,
            "created_at": message.created_at,
        }
        for message in messages
    ]