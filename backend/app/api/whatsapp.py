from fastapi import APIRouter, Depends, Form
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from twilio.twiml.messaging_response import MessagingResponse

from app.database.session import get_db
from app.services.audio.speech_to_text import SpeechToTextService
from app.services.conversation.orchestrator import ConversationOrchestrator
from app.services.websocket.connection_manager import manager

router = APIRouter(prefix="/webhook", tags=["WhatsApp"])


def _safe_int(value: str | int | None, default: int = 0) -> int:
    try:
        return int(value) if value is not None else default
    except (TypeError, ValueError):
        return default


@router.post("/whatsapp")
async def receive_whatsapp_message(
    From: str = Form(default=""),
    Body: str = Form(default=""),
    ProfileName: str = Form(default=""),
    MessageType: str = Form(default=""),
    NumMedia: str = Form(default="0"),
    MediaUrl0: str = Form(default=""),
    MediaContentType0: str = Form(default=""),
    db: Session = Depends(get_db),
):
    if not From:
        return PlainTextResponse("", media_type="application/xml")

    incoming_text = (Body or "").strip()
    incoming_message_type = "TEXT"
    message_type = (MessageType or "").lower().strip()

    has_media = _safe_int(NumMedia, 0) > 0
    media_content_type = (MediaContentType0 or "").lower().strip()
    is_audio_media = has_media and MediaUrl0 and (
        media_content_type.startswith("audio/")
        or media_content_type.startswith("application/ogg")
        or "ogg" in media_content_type
        or message_type == "audio"
    )

    if is_audio_media:
        stt_service = SpeechToTextService()
        stt_result = stt_service.transcribe_twilio_media(
            media_url=MediaUrl0,
            media_content_type=MediaContentType0,
        )

        if not stt_result.get("success"):
            response_text = (
                "Recibi tu audio, pero no pude transcribirlo. "
                "Por favor, intenta con otro audio o escribe tu mensaje en texto."
            )
            twilio_response = MessagingResponse()
            twilio_response.message(response_text)

            await manager.broadcast(
                {
                    "type": "AUDIO_TRANSCRIPTION_FAILED",
                    "phone_number": From,
                    "profile_name": ProfileName,
                    "message": stt_result.get("message", "No se pudo transcribir el audio"),
                }
            )

            return PlainTextResponse(str(twilio_response), media_type="application/xml")

        incoming_text = (stt_result.get("text") or "").strip()
        incoming_message_type = "AUDIO"

    if not incoming_text:
        response_text = "No recibi texto para procesar. Por favor, envia un mensaje de texto o audio."
        twilio_response = MessagingResponse()
        twilio_response.message(response_text)
        return PlainTextResponse(str(twilio_response), media_type="application/xml")

    orchestrator = ConversationOrchestrator(db)

    if incoming_message_type == "AUDIO":
        response_text = orchestrator.handle_audio_message(
            phone_number=From,
            transcript_text=incoming_text,
        )
    else:
        response_text = orchestrator.handle_text_message(
            phone_number=From,
            text=incoming_text,
        )

    twilio_response = MessagingResponse()
    twilio_response.message(response_text)

    await manager.broadcast(
        {
            "type": "NEW_MESSAGE",
            "phone_number": From,
            "message": incoming_text,
            "message_type": incoming_message_type,
            "profile_name": ProfileName,
        }
    )

    return PlainTextResponse(str(twilio_response), media_type="application/xml")
