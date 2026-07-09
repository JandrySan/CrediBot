from unittest.mock import patch

from fastapi.testclient import TestClient

from main import app


class TestWhatsAppAudioWebhook:
    def test_audio_message_uses_transcription_and_audio_handler(self):
        with patch(
            "app.api.whatsapp.SpeechToTextService.transcribe_twilio_media",
            return_value={"success": True, "text": "hola desde audio"},
        ), patch(
            "app.api.whatsapp.ConversationOrchestrator.handle_audio_message",
            return_value="respuesta por audio",
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
        assert audio_handler.called

    def test_audio_transcription_failure_returns_fallback_message(self):
        with patch(
            "app.api.whatsapp.SpeechToTextService.transcribe_twilio_media",
            return_value={"success": False, "message": "fallo stt"},
        ), patch(
            "app.api.whatsapp.ConversationOrchestrator.handle_audio_message",
            return_value="no debe ejecutarse",
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
