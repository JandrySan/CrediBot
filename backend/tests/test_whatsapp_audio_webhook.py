import uuid
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.database.session import SessionLocal
from app.models.customer import Customer
from main import app


class TestWhatsAppAudioWebhook:
    def test_plain_hola_returns_open_welcome_instead_of_asking_name(self):
        with (
            patch(
                "app.services.conversation.orchestrator.AIOrchestrator.analyze_message",
                return_value={"intent": "saludo"},
            ),
            patch(
                "app.services.conversation.orchestrator.AIOrchestrator.get_model_name",
                return_value="test",
            ),
            patch(
                "app.api.whatsapp.TextToSpeechService.generate_voice_note",
                return_value={"success": False, "message": "tts desactivado en test"},
            ),
            TestClient(app) as client,
        ):
            response = client.post(
                "/webhook/whatsapp",
                data={
                    "From": "whatsapp:+593000000010",
                    "Body": "hola",
                    "ProfileName": "Test",
                    "MessageType": "text",
                },
            )

        assert response.status_code == 200
        assert "Escribe lo que necesitas" in response.text
        assert "nombre completo" not in response.text.lower()

    def test_hola_clears_invalid_audio_preference_saved_as_name(self):
        db = SessionLocal()
        phone_number = f"+5939{uuid.uuid4().int % 100000000:08d}"
        try:
            customer = Customer(
                phone_number=phone_number,
                full_name="Respondem por audio",
            )
            db.add(customer)
            db.commit()
        finally:
            db.close()

        with (
            patch(
                "app.services.conversation.orchestrator.AIOrchestrator.analyze_message",
                return_value={"intent": "saludo"},
            ),
            patch(
                "app.services.conversation.orchestrator.AIOrchestrator.get_model_name",
                return_value="test",
            ),
            patch(
                "app.api.whatsapp.TextToSpeechService.generate_voice_note",
                return_value={"success": False, "message": "tts desactivado en test"},
            ),
            TestClient(app) as client,
        ):
            response = client.post(
                "/webhook/whatsapp",
                data={
                    "From": f"whatsapp:{phone_number}",
                    "Body": "hola",
                    "ProfileName": "Test",
                    "MessageType": "text",
                },
            )

        db = SessionLocal()
        try:
            refreshed = db.query(Customer).filter(Customer.phone_number == phone_number).first()
            assert refreshed is not None
            assert refreshed.full_name is None
        finally:
            db.close()

        assert response.status_code == 200
        assert "Escribe lo que necesitas" in response.text
        assert "monto deseas solicitar" not in response.text

    def test_audio_message_uses_transcription_and_audio_handler(self):
        with (
            patch(
                "app.api.whatsapp.SpeechToTextService.transcribe_twilio_media",
                return_value={"success": True, "text": "hola desde audio"},
            ),
            patch(
                "app.services.whatsapp.whatsapp_service.WhatsAppService.process_audio_transcript",
                return_value="respuesta por audio",
            ),
            patch(
                "app.api.whatsapp.TextToSpeechService.generate_voice_note",
                return_value={"success": False, "message": "tts desactivado en test"},
            ) as audio_handler,
            TestClient(app) as client,
        ):
            response = client.post(
                "/webhook/whatsapp",
                data={
                    "From": "whatsapp:+593000000001",
                    "Body": "",
                    "ProfileName": "Test",
                    "MessageType": "audio",
                    "NumMedia": "1",
                    "MediaUrl0": "https://example.com/fake-audio",
                    "MediaContentType0": "audio/ogg",
                },
            )

        assert response.status_code == 200
        assert "respuesta por audio" in response.text
        assert not audio_handler.called

    def test_audio_transcription_failure_returns_fallback_message(self):
        with (
            patch(
                "app.api.whatsapp.SpeechToTextService.transcribe_twilio_media",
                return_value={"success": False, "message": "fallo stt"},
            ),
            patch(
                "app.services.whatsapp.whatsapp_service.WhatsAppService.process_audio_transcript",
                return_value="no debe ejecutarse",
            ),
            patch(
                "app.api.whatsapp.TextToSpeechService.generate_voice_note",
                return_value={"success": False, "message": "tts desactivado en test"},
            ) as audio_handler,
            TestClient(app) as client,
        ):
            response = client.post(
                "/webhook/whatsapp",
                data={
                    "From": "whatsapp:+593000000002",
                    "Body": "",
                    "ProfileName": "Test",
                    "MessageType": "audio",
                    "NumMedia": "1",
                    "MediaUrl0": "https://example.com/fake-audio",
                    "MediaContentType0": "audio/ogg",
                },
            )

        assert response.status_code == 200
        assert "no pude transcribirlo" in response.text.lower()
        assert not audio_handler.called

    def test_text_message_returns_text_by_default_when_tts_is_available(self):
        with (
            patch(
                "app.services.whatsapp.whatsapp_service.WhatsAppService.process_inbound_message",
                return_value="respuesta en texto por defecto",
            ),
            patch(
                "app.api.whatsapp.TextToSpeechService.generate_voice_note",
                return_value={
                    "success": True,
                    "media_url": "https://example.com/webhook/audio/sample.ogg",
                },
            ),
            TestClient(app) as client,
        ):
            response = client.post(
                "/webhook/whatsapp",
                data={
                    "From": "whatsapp:+593000000003",
                    "Body": "hola bot",
                    "ProfileName": "Test",
                    "MessageType": "text",
                },
            )

        assert response.status_code == 200
        assert "respuesta en texto por defecto" in response.text
        assert "<Media>" not in response.text

    def test_user_can_enable_audio_replies(self):
        with (
            patch(
                "app.api.whatsapp.TextToSpeechService.generate_voice_note",
                return_value={
                    "success": True,
                    "media_url": "https://example.com/webhook/audio/sample.ogg",
                },
            ),
            TestClient(app) as client,
        ):
            response = client.post(
                "/webhook/whatsapp",
                data={
                    "From": "whatsapp:+593000000006",
                    "Body": "responde en audio",
                    "ProfileName": "Test",
                    "MessageType": "text",
                },
            )

        assert response.status_code == 200
        assert "respondere en audio" in response.text
        assert "<Media>" not in response.text

    def test_long_audio_preference_request_is_treated_as_mode_command(self):
        with (
            patch(
                "app.services.whatsapp.whatsapp_service.WhatsAppService.process_inbound_message",
                return_value="no debe procesar credito",
            ) as processor,
            patch(
                "app.api.whatsapp.TextToSpeechService.generate_voice_note",
                return_value={
                    "success": True,
                    "media_url": "https://example.com/webhook/audio/preference.ogg",
                },
            ),
            TestClient(app) as client,
        ):
            response = client.post(
                "/webhook/whatsapp",
                data={
                    "From": "whatsapp:+593000000008",
                    "Body": "quiero que me respondas en audio",
                    "ProfileName": "Test",
                    "MessageType": "text",
                },
            )

        assert response.status_code == 200
        assert "respondere en audio" in response.text
        assert "<Media>" not in response.text
        assert not processor.called

    def test_audio_mode_request_with_credit_content_still_processes_message(self):
        with (
            patch(
                "app.services.whatsapp.whatsapp_service.WhatsAppService.process_inbound_message",
                return_value="procesando credito",
            ) as processor,
            patch(
                "app.api.whatsapp.TextToSpeechService.generate_voice_note",
                return_value={
                    "success": True,
                    "media_url": "https://example.com/webhook/audio/credit.ogg",
                },
            ),
            TestClient(app) as client,
        ):
            response = client.post(
                "/webhook/whatsapp",
                data={
                    "From": "whatsapp:+593000000009",
                    "Body": "responde en audio, quiero un credito de 2000",
                    "ProfileName": "Test",
                    "MessageType": "text",
                },
            )

        assert response.status_code == 200
        assert "<Media>https://example.com/webhook/audio/credit.ogg</Media>" in response.text
        assert processor.called

    def test_user_can_return_to_text_replies_after_audio_mode(self):
        with (
            patch(
                "app.api.whatsapp.TextToSpeechService.generate_voice_note",
                return_value={
                    "success": True,
                    "media_url": "https://example.com/webhook/audio/sample.ogg",
                },
            ),
            TestClient(app) as client,
        ):
            client.post(
                "/webhook/whatsapp",
                data={
                    "From": "whatsapp:+593000000007",
                    "Body": "responde en audio",
                    "ProfileName": "Test",
                    "MessageType": "text",
                },
            )

            response = client.post(
                "/webhook/whatsapp",
                data={
                    "From": "whatsapp:+593000000007",
                    "Body": "responde en texto",
                    "ProfileName": "Test",
                    "MessageType": "text",
                },
            )

        assert response.status_code == 200
        assert "respondere en texto" in response.text
        assert "<Media>" not in response.text

    def test_text_message_falls_back_to_text_when_tts_fails(self):
        with (
            patch(
                "app.services.whatsapp.whatsapp_service.WhatsAppService.process_inbound_message",
                return_value="respuesta en texto",
            ),
            patch(
                "app.api.whatsapp.TextToSpeechService.generate_voice_note",
                return_value={"success": False, "message": "tts apagado"},
            ),
            TestClient(app) as client,
        ):
            response = client.post(
                "/webhook/whatsapp",
                data={
                    "From": "whatsapp:+593000000004",
                    "Body": "hola bot",
                    "ProfileName": "Test",
                    "MessageType": "text",
                },
            )

        assert response.status_code == 200
        assert "respuesta en texto" in response.text
        assert "<Media>" not in response.text

    def test_handoff_message_returns_empty_twiml_without_auto_reply(self):
        with (
            patch(
                "app.services.whatsapp.whatsapp_service.WhatsAppService.process_inbound_message",
                return_value="",
            ),
            patch(
                "app.api.whatsapp.TextToSpeechService.generate_voice_note",
                return_value={"success": False, "message": "sin respuesta automatica"},
            ),
            TestClient(app) as client,
        ):
            response = client.post(
                "/webhook/whatsapp",
                data={
                    "From": "whatsapp:+593000000005",
                    "Body": "quiero hablar con asesor",
                    "ProfileName": "Test",
                    "MessageType": "text",
                },
            )

        assert response.status_code == 200
        assert "<Message>" not in response.text
