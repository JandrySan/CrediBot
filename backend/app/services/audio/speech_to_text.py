import tempfile
from pathlib import Path

import httpx


class SpeechToTextService:
    def __init__(self, model_size: str = "base"):
        self.model_size = model_size
        self._model = None

    @property
    def _model_instance(self):
        if self._model is None:
            try:
                from faster_whisper import WhisperModel
                self._model = WhisperModel(self.model_size)
            except ImportError:
                raise ImportError(
                    "faster-whisper is required. "
                    "Install it with: pip install faster-whisper"
                )
        return self._model

    def transcribe_file(self, audio_path: str | Path) -> str:
        segments, _ = self._model_instance.transcribe(str(audio_path), language="es")
        return " ".join(seg.text for seg in segments).strip()

    async def transcribe_url(self, audio_url: str) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.get(audio_url)
            response.raise_for_status()

        suffix = self._detect_extension(audio_url)
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(response.content)
            tmp_path = tmp.name

        try:
            return self.transcribe_file(tmp_path)
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def _detect_extension(self, url: str) -> str:
        url_lower = url.lower()
        if ".ogg" in url_lower:
            return ".ogg"
        if ".mp3" in url_lower or ".mp4" in url_lower:
            return ".mp3"
        if ".wav" in url_lower:
            return ".wav"
        if ".m4a" in url_lower:
            return ".m4a"
        return ".ogg"
