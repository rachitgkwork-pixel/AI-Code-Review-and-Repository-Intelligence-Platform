"""Embedding service backed by sentence-transformers.

Loads the model once at startup and exposes encode() for generating vectors.
"""

from functools import lru_cache

from sentence_transformers import SentenceTransformer

from backend.config import get_settings
from backend.utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


@lru_cache(maxsize=1)
def _load_model() -> SentenceTransformer:
    logger.info("Loading embedding model: %s", settings.embedding_model)
    return SentenceTransformer(settings.embedding_model)


class EmbeddingService:
    def __init__(self) -> None:
        self._model = _load_model()

    def encode(self, texts: list[str]) -> list[list[float]]:
        """Return a list of float vectors, one per input text."""
        vectors = self._model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
        return [v.tolist() for v in vectors]

    def encode_one(self, text: str) -> list[float]:
        return self.encode([text])[0]


_service: EmbeddingService | None = None


def get_embedding_service() -> EmbeddingService:
    global _service
    if _service is None:
        _service = EmbeddingService()
    return _service
