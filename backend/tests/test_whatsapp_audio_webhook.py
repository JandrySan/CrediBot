from unittest.mock import patch

from fastapi.testclient import TestClient

from main import app


class TestWhatsAppAudioWebhook:
    def test_audio_message_uses_transcription_and_audio_handler(self):
        with patch(
            "app.api.whatsapp.SpeechToTextService.transcribe_twilio_media",
            return_value={"success": True, "text": "hola desde audio"},
        ), patch(
            "app.services.whatsapp.whatsapp_service.WhatsAppService.process_audio_transcript",
            return_value="respuesta por audio",
        ), patch(
            "app.api.whatsapp.TextToSpeechService.generate_voice_note",
            return_value={"success": False, "message": "tts desactivado en test"},
        ) as audio_handler:
            with TestClient(app) as client:
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
        with patch(
            "app.api.whatsapp.SpeechToTextService.transcribe_twilio_media",
            return_value={"success": False, "message": "fallo stt"},
        ), patch(
            "app.services.whatsapp.whatsapp_service.WhatsAppService.process_audio_transcript",
            return_value="no debe ejecutarse",
        ), patch(
            "app.api.whatsapp.TextToSpeechService.generate_voice_note",
            return_value={"success": False, "message": "tts desactivado en test"},
        ) as audio_handler:
            with TestClient(app) as client:
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
        with patch(
            "app.services.whatsapp.whatsapp_service.WhatsAppService.process_inbound_message",
            return_value="respuesta en texto por defecto",
        ), patch(
            "app.api.whatsapp.TextToSpeechService.generate_voice_note",
            return_value={
                "success": True,
                "media_url": "https://example.com/webhook/audio/sample.ogg",
            },
        ):
            with TestClient(app) as client:
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
        with patch(
            "app.api.whatsapp.TextToSpeechService.generate_voice_note",
            return_value={
                "success": True,
                "media_url": "https://example.com/webhook/audio/sample.ogg",
            },
        ):
            with TestClient(app) as client:
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
        assert "<Media>https://example.com/webhook/audio/sample.ogg</Media>" in response.text

    def test_user_can_return_to_text_replies_after_audio_mode(self):
        with patch(
            "app.api.whatsapp.TextToSpeechService.generate_voice_note",
            return_value={
                "success": True,
                "media_url": "https://example.com/webhook/audio/sample.ogg",
            },
        ):
            with TestClient(app) as client:
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
        with patch(
            "app.services.whatsapp.whatsapp_service.WhatsAppService.process_inbound_message",
            return_value="respuesta en texto",
        ), patch(
            "app.api.whatsapp.TextToSpeechService.generate_voice_note",
            return_value={"success": False, "message": "tts apagado"},
        ):
            with TestClient(app) as client:
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
        with patch(
            "app.services.whatsapp.whatsapp_service.WhatsAppService.process_inbound_message",
            return_value="",
        ), patch(
            "app.api.whatsapp.TextToSpeechService.generate_voice_note",
            return_value={"success": False, "message": "sin respuesta automatica"},
        ):
            with TestClient(app) as client:
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
