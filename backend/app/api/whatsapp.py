from fastapi import APIRouter, Depends, Form
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from twilio.twiml.messaging_response import MessagingResponse

from app.database.session import get_db
from app.services.conversation.orchestrator import ConversationOrchestrator
from app.services.websocket.connection_manager import manager

router = APIRouter(prefix="/webhook", tags=["WhatsApp"])


@router.post("/whatsapp")
async def receive_whatsapp_message(
    From: str = Form(default=""),
    Body: str = Form(default=""),
    ProfileName: str = Form(default=""),
    db: Session = Depends(get_db)
):
    if not From:
        return PlainTextResponse("", media_type="application/xml")

    orchestrator = ConversationOrchestrator(db)

    response_text = orchestrator.handle_text_message(
        phone_number=From,
        text=Body
    )

    twilio_response = MessagingResponse()
    twilio_response.message(response_text)

    await manager.broadcast({
        "type": "NEW_MESSAGE",
        "phone_number": From,
        "message": Body,
        "profile_name": ProfileName,
    })

    return PlainTextResponse(str(twilio_response), media_type="application/xml")