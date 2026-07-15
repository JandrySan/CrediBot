import os
import tempfile
from contextlib import suppress
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import httpx
from groq import APIError

from app.config.settings import settings

ALLOWED_TWILIO_MEDIA_HOSTS = frozenset({"api.twilio.com"})


class SpeechToTextService:
    _shared_model: Any = None
    _shared_signature: tuple[str, str, str] | None = None
    _groq_client: Any = None

    def __init__(self):
        self.enabled = bool(settings.AUDIO_STT_ENABLED)
        self.provider = (settings.AUDIO_STT_PROVIDER or "groq").strip().lower()

        self.model_name = settings.AUDIO_STT_MODEL
        self.language = "es"
        self.device = settings.AUDIO_STT_DEVICE
        self.compute_type = settings.AUDIO_STT_COMPUTE_TYPE

        self.groq_model = settings.AUDIO_STT_GROQ_MODEL
        self.request_timeout = int(settings.AUDIO_STT_REQUEST_TIMEOUT_SECONDS)

    def transcribe_twilio_media(
        self,
        media_url: str,
        media_content_type: str | None = None,
    ) -> dict[str, Any]:
        if not self.enabled:
            return {
                "success": False,
                "message": "La transcripcion de audio esta desactivada.",
            }

        if not media_url:
            return {
                "success": False,
                "message": "No se recibio una URL de audio valida.",
            }

        temp_path: Path | None = None

        try:
            temp_path = self._download_twilio_media(
                media_url=media_url,
                media_content_type=media_content_type,
            )
            text = self._transcribe_file(temp_path)

            if not text:
                return {
                    "success": False,
                    "message": "No se pudo transcribir el audio recibido.",
                }

            return {
                "success": True,
                "text": text,
            }
        except (
            APIError,
            httpx.HTTPError,
            ImportError,
            OSError,
            RuntimeError,
            TypeError,
            ValueError,
        ) as exc:
            return {
                "success": False,
                "message": f"Error al procesar audio: {exc}",
            }
        finally:
            if temp_path and temp_path.exists():
                with suppress(OSError):
                    temp_path.unlink()

    def _download_twilio_media(
        self,
        media_url: str,
        media_content_type: str | None = None,
    ) -> Path:
        validated_media_url = self._validate_twilio_media_url(media_url)
        auth = None
        if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
            auth = (settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

        with httpx.Client(
            timeout=self.request_timeout,
            follow_redirects=True,
            auth=auth,
        ) as client:
            response = client.get(
                validated_media_url
            )  # NOSONAR: URL is HTTPS and host allowlisted.
            response.raise_for_status()
            content = response.content
            response_content_type = response.headers.get("content-type", "")

        final_content_type = (media_content_type or response_content_type or "").lower()
        suffix = self._suffix_for_content_type(final_content_type)

        fd, path = tempfile.mkstemp(prefix="credibot_audio_", suffix=suffix)
        os.close(fd)

        output_path = Path(path)
        output_path.write_bytes(content)
        return output_path

    @staticmethod
    def _validate_twilio_media_url(media_url: str) -> str:
        parsed = urlsplit(media_url)
        hostname = (parsed.hostname or "").lower()

        if parsed.scheme != "https":
            raise ValueError("La URL de audio de Twilio debe usar HTTPS.")
        if parsed.username or parsed.password:
            raise ValueError("La URL de audio de Twilio no debe incluir credenciales.")
        if hostname not in ALLOWED_TWILIO_MEDIA_HOSTS:
            raise ValueError("La URL de audio no pertenece a un host permitido de Twilio.")
        if not parsed.path.startswith("/2010-04-01/Accounts/"):
            raise ValueError("La ruta de audio de Twilio no tiene el formato esperado.")

        return parsed.geturl()

    def _transcribe_file(self, audio_path: Path) -> str:
        provider = self.provider

        if provider == "groq":
            return self._transcribe_with_groq(audio_path)

        if provider == "local":
            return self._transcribe_with_local(audio_path)

        if provider == "groq_local_fallback":
            text = self._transcribe_with_groq(audio_path)
            if text:
                return text
            return self._transcribe_with_local(audio_path)

        # Provider desconocido: usar groq como fallback por defecto
        return self._transcribe_with_groq(audio_path)

    def _transcribe_with_groq(self, audio_path: Path) -> str:
        if not settings.GROQ_API_KEY:
            return ""

        client = self._get_groq_client()

        kwargs: dict[str, Any] = {
            "model": self.groq_model,
            "temperature": 0,
        }

        if self.language:
            kwargs["language"] = self.language

        with audio_path.open("rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                file=(audio_path.name, audio_file.read()),
                **kwargs,
            )

        if hasattr(transcript, "text"):
            return (transcript.text or "").strip()

        if isinstance(transcript, dict):
            return (transcript.get("text") or "").strip()

        return ""

    def _transcribe_with_local(self, audio_path: Path) -> str:
        model = self._get_local_model()

        segments, _ = model.transcribe(
            str(audio_path),
            language=self.language,
            beam_size=5,
            vad_filter=True,
        )

        parts: list[str] = []
        for segment in segments:
            text = (segment.text or "").strip()
            if text:
                parts.append(text)

        return " ".join(parts).strip()

    @classmethod
    def _get_groq_client(cls):
        if cls._groq_client is None:
            from groq import Groq

            cls._groq_client = Groq(
                api_key=settings.GROQ_API_KEY,
                timeout=settings.AUDIO_STT_REQUEST_TIMEOUT_SECONDS,
            )

        return cls._groq_client

    def _get_local_model(self):
        signature = (self.model_name, self.device, self.compute_type)

        if (
            SpeechToTextService._shared_model is None
            or SpeechToTextService._shared_signature != signature
        ):
            from faster_whisper import WhisperModel

            SpeechToTextService._shared_model = WhisperModel(
                self.model_name,
                device=self.device,
                compute_type=self.compute_type,
            )
            SpeechToTextService._shared_signature = signature

        return SpeechToTextService._shared_model

    @staticmethod
    def _suffix_for_content_type(content_type: str) -> str:
        mapping = {
            "audio/ogg": ".ogg",
            "application/ogg": ".ogg",
            "audio/opus": ".ogg",
            "audio/mpeg": ".mp3",
            "audio/mp3": ".mp3",
            "audio/wav": ".wav",
            "audio/x-wav": ".wav",
            "audio/mp4": ".m4a",
            "audio/x-m4a": ".m4a",
            "audio/webm": ".webm",
        }

        for mime, suffix in mapping.items():
            if content_type.startswith(mime):
                return suffix

        return ".bin"
