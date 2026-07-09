import time
import uuid
import re
from pathlib import Path
from urllib.parse import urlparse

from app.config.settings import settings


class TextToSpeechService:
    def __init__(self):
        self.enabled = bool(settings.AUDIO_REPLY_ENABLED)
        self.language = (settings.AUDIO_REPLY_LANGUAGE or "es").strip() or "es"

        backend_root = Path(__file__).resolve().parents[3]
        self.output_dir = backend_root / "work" / "audio_out"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_voice_note(self, text: str) -> dict:
        if not self.enabled:
            return {"success": False, "message": "Respuesta en audio desactivada."}

        clean_text = self._prepare_text_for_voice((text or "").strip())
        if not clean_text:
            return {"success": False, "message": "No hay texto para sintetizar."}

        audio_id = uuid.uuid4().hex
        mp3_path = self.output_dir / f"{audio_id}.mp3"
        ogg_path = self.output_dir / f"{audio_id}.ogg"

        try:
            self._cleanup_old_files()
            self._synthesize_mp3(clean_text, mp3_path)
            self._convert_mp3_to_ogg_opus(mp3_path, ogg_path)

            media_url = self._build_public_media_url(ogg_path.name)
            if not media_url:
                return {
                    "success": False,
                    "message": "No se pudo construir la URL publica para enviar audio.",
                }

            return {
                "success": True,
                "media_url": media_url,
            }
        except Exception as exc:
            return {
                "success": False,
                "message": f"Error al generar audio: {exc}",
            }
        finally:
            if mp3_path.exists():
                try:
                    mp3_path.unlink()
                except OSError:
                    pass

    def _prepare_text_for_voice(self, text: str) -> str:
        prepared = text

        explicit_replacements = {
            "PREAPROBADO": "preaprobado",
            "OBSERVADO": "observado",
            "RECHAZADO": "rechazado",
        }

        for source, target in explicit_replacements.items():
            prepared = re.sub(rf"\b{source}\b", target, prepared)

        # Lower long uppercase words to avoid letter-by-letter pronunciation in TTS.
        prepared = re.sub(
            r"\b[A-Z]{4,}\b",
            lambda match: match.group(0).lower(),
            prepared,
        )

        return prepared.strip()

    def _synthesize_mp3(self, text: str, target_path: Path):
        from gtts import gTTS

        tts = gTTS(text=text, lang=self.language)
        tts.save(str(target_path))

    def _convert_mp3_to_ogg_opus(self, source_path: Path, target_path: Path):
        import av

        input_container = av.open(str(source_path))
        output_container = av.open(str(target_path), mode="w", format="ogg")

        try:
            output_stream = output_container.add_stream("libopus", rate=48000)
            output_stream.layout = "mono"
            output_stream.bit_rate = 32000

            resampler = av.audio.resampler.AudioResampler(
                format="fltp",
                layout="mono",
                rate=48000,
            )

            for frame in input_container.decode(audio=0):
                frame.pts = None
                for out_frame in resampler.resample(frame):
                    for packet in output_stream.encode(out_frame):
                        output_container.mux(packet)

            for packet in output_stream.encode(None):
                output_container.mux(packet)
        finally:
            output_container.close()
            input_container.close()

    def _build_public_media_url(self, filename: str) -> str:
        base_url = (settings.AUDIO_REPLY_PUBLIC_BASE_URL or "").strip()

        if not base_url:
            webhook_url = (settings.TWILIO_WEBHOOK_URL or "").strip()
            if webhook_url:
                parsed = urlparse(webhook_url)
                if parsed.scheme and parsed.netloc:
                    base_url = f"{parsed.scheme}://{parsed.netloc}"

        if not base_url:
            return ""

        return f"{base_url.rstrip('/')}/webhook/audio/{filename}"

    def _cleanup_old_files(self, max_age_seconds: int = 3600):
        now = time.time()
        for file_path in self.output_dir.glob("*"):
            if not file_path.is_file():
                continue

            try:
                age = now - file_path.stat().st_mtime
                if age > max_age_seconds:
                    file_path.unlink(missing_ok=True)
            except OSError:
                continue
