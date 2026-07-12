from fastapi import APIRouter, Depends, Form
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from twilio.twiml.messaging_response import MessagingResponse

from app.database.session import get_db
from app.services.conversation.orchestrator import ConversationOrchestrator
from app.services.websocket.connection_manager import manager
from app.services.audio.speech_to_text import SpeechToTextService

router = APIRouter(prefix="/webhook", tags=["WhatsApp"])


@router.post("/whatsapp")
async def receive_whatsapp_message(
    From: str = Form(default=""),
    Body: str = Form(default=""),
    ProfileName: str = Form(default=""),
    MediaUrl0: str = Form(default=""),
    MediaContentType0: str = Form(default=""),
    db: Session = Depends(get_db)
):
    if not From:
        return PlainTextResponse("", media_type="application/xml")

    text = Body

    if MediaUrl0 and not text.strip():
        if "audio" in MediaContentType0:
            stt = SpeechToTextService()
            text = await stt.transcribe_url(MediaUrl0)

    orchestrator = ConversationOrchestrator(db)

    response_text = orchestrator.handle_text_message(
        phone_number=From,
        text=text or ""
    )

    twilio_response = MessagingResponse()
    twilio_response.message(response_text)

    await manager.broadcast({
        "type": "NEW_MESSAGE",
        "phone_number": From,
        "message": text,
        "profile_name": ProfileName,
        "media_type": MediaContentType0 if MediaUrl0 else "text",
    })

    return PlainTextResponse(str(twilio_response), media_type="application/xml")
