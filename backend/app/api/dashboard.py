from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.state_machine.states import ConversationState
from app.database.session import get_db
from app.models.customer import Customer
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.credit_application import CreditApplication
from app.services.rag.faq_loader import FAQLoader
from app.services.rag.models import KnowledgeBase
from app.services.conversation.conversation_manager import ConversationManager
from app.services.whatsapp.twilio_service import TwilioWhatsAppService

from fastapi import Form
from app.services.websocket.connection_manager import manager

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


def _serialize_faq(faq: KnowledgeBase) -> dict:
    return {
        "id": faq.id,
        "question": faq.question,
        "answer": faq.answer,
        "category": faq.category,
        "keywords": faq.keyword_list(),
        "is_active": faq.is_active,
        "created_at": faq.created_at,
        "updated_at": faq.updated_at,
    }


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
        "closed_conversations": db.query(Conversation).filter(
            Conversation.status == "CLOSED"
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


@router.post("/conversations/cleanup-expired")
def cleanup_expired_conversations(db: Session = Depends(get_db)):
    closed_count = ConversationManager(db).cleanup_expired_sessions()

    return {
        "success": True,
        "closed_count": closed_count,
    }


@router.post("/faq/upload")
async def upload_faq(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    raw_content = (await file.read()).decode("utf-8-sig")
    filename = (file.filename or "").lower()
    loader = FAQLoader(db)

    try:
        if filename.endswith(".csv"):
            result = loader.load_csv(raw_content)
        else:
            result = loader.load_json(raw_content)
    except ValueError as exc:
        return {
            "success": False,
            "message": str(exc),
        }

    return {
        "success": True,
        "message": "FAQs cargadas correctamente",
        **result,
    }


@router.get("/faq")
def list_faqs(db: Session = Depends(get_db)):
    faqs = (
        db.query(KnowledgeBase)
        .filter(KnowledgeBase.is_active.is_(True))
        .order_by(KnowledgeBase.id.desc())
        .all()
    )

    return [_serialize_faq(faq) for faq in faqs]


@router.delete("/faq/{faq_id}")
def delete_faq(faq_id: int, db: Session = Depends(get_db)):
    faq = (
        db.query(KnowledgeBase)
        .filter(KnowledgeBase.id == faq_id)
        .first()
    )

    if not faq:
        return {
            "success": False,
            "message": "FAQ no encontrada",
        }

    faq.is_active = False
    db.commit()

    return {
        "success": True,
        "message": "FAQ eliminada",
        "faq_id": faq_id,
    }

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

    if conversation.status == "CLOSED":
        return {
            "success": False,
            "message": "La conversación está cerrada. Espera una nueva conversación del cliente."
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

    if conversation.status != "HANDOFF":
        return {
            "success": False,
            "message": "Solo puedes responder manualmente cuando la conversacion esta en HANDOFF."
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


@router.post("/conversations/{conversation_id}/close")
async def close_conversation(
    conversation_id: int,
    resolution: str = Form(default="RESOLVED"),
    note: str = Form(default=""),
    db: Session = Depends(get_db),
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

    if conversation.status != "HANDOFF":
        return {
            "success": False,
            "message": "Solo puedes cerrar conversaciones en estado HANDOFF."
        }

    normalized_resolution = (resolution or "").strip().upper()
    resolution_map = {
        "APPROVED": ("APROBADO_ASESOR", "Credito aprobado por asesor"),
        "DENIED": ("NEGADO_ASESOR", "Credito negado por asesor"),
        "RESOLVED": ("RESUELTO_ASESOR", "Duda resuelta por asesor"),
    }

    if normalized_resolution not in resolution_map:
        normalized_resolution = "RESOLVED"

    conversation_result, resolution_reason = resolution_map[normalized_resolution]

    latest_application = (
        db.query(CreditApplication)
        .filter(CreditApplication.customer_id == conversation.customer_id)
        .order_by(CreditApplication.id.desc())
        .first()
    )

    if latest_application and latest_application.result is None:
        if normalized_resolution == "APPROVED":
            latest_application.result = "PREAPROBADO"
        elif normalized_resolution == "DENIED":
            latest_application.result = "OBSERVADO"
        else:
            latest_application.result = "RESUELTO_ASESOR"

        if (note or "").strip():
            latest_application.reason = f"{resolution_reason}. Nota: {(note or '').strip()}"
        else:
            latest_application.reason = resolution_reason

    conversation.status = "CLOSED"
    conversation.current_state = ConversationState.END.value
    conversation.result = conversation_result

    db.commit()
    db.refresh(conversation)

    await manager.broadcast({
        "type": "CONVERSATION_CLOSED",
        "conversation_id": conversation.id,
        "status": conversation.status,
        "state": conversation.current_state,
        "resolution": normalized_resolution,
    })

    return {
        "success": True,
        "message": "Conversación cerrada. El siguiente mensaje del cliente iniciará un nuevo flujo con el bot.",
        "conversation_id": conversation.id,
        "status": conversation.status,
        "state": conversation.current_state,
        "resolution": normalized_resolution,
    }
