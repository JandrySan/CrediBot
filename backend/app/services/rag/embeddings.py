import numpy as np


class EmbeddingService:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None

    @property
    def _model_instance(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
            except ImportError:
                raise ImportError(
                    "sentence-transformers is required. "
                    "Install it with: pip install sentence-transformers"
                )
        return self._model

    @property
    def dimension(self) -> int:
        return 384

    def embed(self, text: str) -> list[float]:
        return self._model_instance.encode(text).tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        embeddings = self._model_instance.encode(texts)
        return [e.tolist() for e in embeddings]
