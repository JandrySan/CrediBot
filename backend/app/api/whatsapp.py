from fastapi import APIRouter, Depends, Form
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from twilio.twiml.messaging_response import MessagingResponse

from app.database.session import get_db
from app.services.conversation.conversation_manager import ConversationManager

router = APIRouter(prefix="/webhook", tags=["WhatsApp"])


@router.post("/whatsapp")
def receive_whatsapp_message(
    From: str = Form(...),
    Body: str = Form(""),
    db: Session = Depends(get_db)
):
    manager = ConversationManager(db)
    response_text = manager.process_message(
        phone_number=From,
        text=Body
    )

    twilio_response = MessagingResponse()
    twilio_response.message(response_text)

    return PlainTextResponse(str(twilio_response), media_type="application/xml")