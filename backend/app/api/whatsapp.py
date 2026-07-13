from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse
from sqlalchemy.orm import Session
from twilio.twiml.messaging_response import MessagingResponse

from app.database.session import get_db
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.customer_repository import CustomerRepository
from app.repositories.message_repository import MessageRepository
from app.services.audio.speech_to_text import SpeechToTextService
from app.services.audio.text_to_speech import TextToSpeechService
from app.services.whatsapp.response_mode import ResponseModePreference
from app.services.whatsapp.whatsapp_service import WhatsAppService
from app.services.websocket.connection_manager import manager

router = APIRouter(prefix="/webhook", tags=["WhatsApp"])


def _safe_int(value: str | int | None, default: int = 0) -> int:
    try:
        return int(value) if value is not None else default
    except (TypeError, ValueError):
        return default


def _get_or_create_conversation(db: Session, phone_number: str):
    customer = CustomerRepository(db).get_or_create(phone_number)
    return ConversationRepository(db).get_or_create_active(customer.id)


def _apply_response_mode_preference(db: Session, phone_number: str, text: str):
    requested_mode = ResponseModePreference.detect(text)
    if not requested_mode:
        return None, False

    conversation = _get_or_create_conversation(db, phone_number)
    if conversation.response_mode != requested_mode:
        conversation = ConversationRepository(db).update_response_mode(
            conversation=conversation,
            response_mode=requested_mode,
        )

    return conversation, ResponseModePreference.is_command_only(text, requested_mode)


def _resolve_response_mode(db: Session, phone_number: str) -> str:
    customer = CustomerRepository(db).get_by_phone(phone_number)
    if not customer:
        return ResponseModePreference.TEXT

    conversation = ConversationRepository(db).get_open_by_customer(customer.id)
    mode = (getattr(conversation, "response_mode", "") or "").strip().upper()

    if mode == ResponseModePreference.AUDIO:
        return ResponseModePreference.AUDIO

    return ResponseModePreference.TEXT


def _preference_confirmation(response_mode: str) -> str:
    if response_mode == ResponseModePreference.AUDIO:
        return (
            "Listo, a partir de ahora te respondere en audio. "
            "Cuando quieras volver a texto, escribe: responde en texto."
        )

    return (
        "Listo, a partir de ahora te respondere en texto. "
        "Cuando quieras audio, escribe: responde en audio."
    )


def _build_twilio_reply(response_text: str, response_mode: str):
    twilio_response = MessagingResponse()
    clean_response_text = (response_text or "").strip()
    tts_result = {"success": False, "message": "Respuesta en texto por preferencia del usuario."}
    bot_response_type = "NONE"

    if not clean_response_text:
        return twilio_response, tts_result, bot_response_type

    if response_mode == ResponseModePreference.AUDIO:
        tts_service = TextToSpeechService()
        tts_result = tts_service.generate_voice_note(clean_response_text)
        is_audio_reply = bool(tts_result.get("success")) and bool(tts_result.get("media_url"))

        if is_audio_reply:
            reply_message = twilio_response.message()
            reply_message.media(tts_result["media_url"])
            return twilio_response, tts_result, "AUDIO"

    twilio_response.message(clean_response_text)
    return twilio_response, tts_result, "TEXT"


@router.get("/audio/{filename}")
async def serve_generated_audio(filename: str):
    if Path(filename).name != filename:
        raise HTTPException(status_code=400, detail="Nombre de archivo invalido")

    tts_service = TextToSpeechService()
    audio_dir = tts_service.output_dir.resolve()
    file_path = (audio_dir / filename).resolve()

    if file_path.parent != audio_dir or not file_path.exists():
        raise HTTPException(status_code=404, detail="Audio no encontrado")

    return FileResponse(str(file_path), media_type="audio/ogg", filename=filename)


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
    force_text_reply = False

    whatsapp_service = WhatsAppService(db)

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
            response_text = (
                "Recibi tu audio, pero no contiene texto reconocible. "
                "Por favor, intenta con otro audio o escribe tu mensaje."
            )
            twilio_response = MessagingResponse()
            twilio_response.message(response_text)
            return PlainTextResponse(str(twilio_response), media_type="application/xml")

        preference_conversation, is_preference_command = _apply_response_mode_preference(
            db=db,
            phone_number=From,
            text=incoming_text,
        )

        if is_preference_command:
            response_text = _preference_confirmation(preference_conversation.response_mode)
            force_text_reply = True
            MessageRepository(db).save_message(
                conversation_id=preference_conversation.id,
                direction="INBOUND",
                content=incoming_text,
                message_type=incoming_message_type,
            )
            MessageRepository(db).save_message(
                conversation_id=preference_conversation.id,
                direction="OUTBOUND",
                content=response_text,
                message_type="TEXT",
            )
        else:
            response_text = whatsapp_service.process_audio_transcript(
                phone_number=From,
                transcript_text=incoming_text,
                profile_name=ProfileName,
            )
    else:
        if not incoming_text:
            response_text = "No recibi texto para procesar. Por favor, envia un mensaje de texto o audio."
            twilio_response = MessagingResponse()
            twilio_response.message(response_text)
            return PlainTextResponse(str(twilio_response), media_type="application/xml")

        preference_conversation, is_preference_command = _apply_response_mode_preference(
            db=db,
            phone_number=From,
            text=incoming_text,
        )

        if is_preference_command:
            response_text = _preference_confirmation(preference_conversation.response_mode)
            force_text_reply = True
            MessageRepository(db).save_message(
                conversation_id=preference_conversation.id,
                direction="INBOUND",
                content=incoming_text,
                message_type=incoming_message_type,
            )
            MessageRepository(db).save_message(
                conversation_id=preference_conversation.id,
                direction="OUTBOUND",
                content=response_text,
                message_type="TEXT",
            )
        else:
            response_text = whatsapp_service.process_inbound_message(
                phone_number=From,
                text=incoming_text,
                message_type=incoming_message_type,
                profile_name=ProfileName,
            )

    clean_response_text = (response_text or "").strip()
    response_mode = (
        ResponseModePreference.TEXT
        if force_text_reply
        else _resolve_response_mode(db, From)
    )
    twilio_response, tts_result, bot_response_type = _build_twilio_reply(
        response_text=clean_response_text,
        response_mode=response_mode,
    )

    await manager.broadcast(
        {
            "type": "NEW_MESSAGE",
            "phone_number": From,
            "message": incoming_text,
            "message_type": incoming_message_type,
            "profile_name": ProfileName,
            "bot_response_type": bot_response_type,
            "bot_response_mode": response_mode,
            "bot_response": clean_response_text,
            "bot_media_url": tts_result.get("media_url", ""),
            "bot_audio_error": tts_result.get("message", ""),
        }
    )

    return PlainTextResponse(str(twilio_response), media_type="application/xml")
