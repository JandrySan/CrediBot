from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.state_machine.states import ConversationState
from app.database.session import get_db
from app.models.customer import Customer
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.credit_application import CreditApplication
from app.services.whatsapp.twilio_service import TwilioWhatsAppService

from fastapi import Form
from app.services.websocket.connection_manager import manager

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

@router.post("/conversations/{conversation_id}/take")
def take_conversation(
    conversation_id: int,
    db: Session = Depends(get_db)
):
    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id)
        .first()
    )

    if not conversation:
        return {
            "success": False,
            "message": "Conversación no encontrada"
        }

    conversation.status = "HANDOFF"
    conversation.current_state = ConversationState.HANDOFF.value

    db.commit()
    db.refresh(conversation)

    return {
        "success": True,
        "message": "Conversación tomada por asesor",
        "conversation_id": conversation.id,
        "status": conversation.status,
        "state": conversation.current_state
    }


@router.post("/conversations/{conversation_id}/reply")
async def reply_conversation(
    conversation_id: int,
    message: str = Form(...),
    db: Session = Depends(get_db)
):
    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id)
        .first()
    )

    if not conversation:
        return {
            "success": False,
            "message": "Conversación no encontrada"
        }

    customer = (
        db.query(Customer)
        .filter(Customer.id == conversation.customer_id)
        .first()
    )

    if not customer:
        return {
            "success": False,
            "message": "Cliente no encontrado"
        }

    outbound_message = Message(
        conversation_id=conversation.id,
        direction="OUTBOUND",
        message_type="TEXT",
        content=message
    )

    db.add(outbound_message)
    db.commit()
    db.refresh(outbound_message)

    twilio_service = TwilioWhatsAppService()
    twilio_result = twilio_service.send_message(
        to=customer.phone_number,
        body=message
    )

    await manager.broadcast({
        "type": "AGENT_REPLY",
        "conversation_id": conversation.id,
        "message": message
    })

    whatsapp_sent = twilio_result.get("success", False)

    return {
        "success": whatsapp_sent,
        "message": (
            "Respuesta enviada por asesor"
            if whatsapp_sent
            else twilio_result.get("message", "No se pudo enviar el mensaje por WhatsApp")
        ),
        "conversation_id": conversation.id,
        "message_saved": True,
        "whatsapp_sent": whatsapp_sent,
        "twilio": twilio_result
    }