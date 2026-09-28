from collections.abc import Sequence
from typing import Protocol

from langchain_ollama import OllamaEmbeddings

from ..config import Settings
from ..repositories.cv_vector_repository import (
    CvVectorDimensionError,
    CvVectorRepository,
)
from .cv_chunking import CvChunk


class EmbeddingClient(Protocol):
    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...


class CvEmbeddingError(RuntimeError):
    """Ollama could not create embeddings for the CV chunks."""


class CvVectorService:
    def __init__(
        self,
        settings: Settings,
        *,
        repository: CvVectorRepository | None = None,
        embeddings: EmbeddingClient | None = None,
    ) -> None:
        self.embedding_dimension = settings.pgvector_embedding_dimension
        self.repository = repository or CvVectorRepository(settings)
        self.embeddings = embeddings or OllamaEmbeddings(
            model=settings.ollama_embedding_model,
            base_url=settings.ollama_embedding_base_url,
        )

    def setup(self) -> None:
        self.repository.setup()

    def replace_active_cv(self, chunks: Sequence[CvChunk]) -> int:
        if not chunks:
            raise ValueError("At least one CV chunk is required")

        try:
            vectors = self.embeddings.embed_documents([chunk.content for chunk in chunks])
        except Exception as exc:
            raise CvEmbeddingError("Could not generate CV embeddings") from exc

        if len(vectors) != len(chunks):
            raise CvEmbeddingError("The embedding service returned an incomplete result")
        for vector in vectors:
            if len(vector) != self.embedding_dimension:
                raise CvVectorDimensionError(
                    f"Embedding dimension {len(vector)} does not match configured "
                    f"dimension {self.embedding_dimension}"
                )

        return self.repository.replace_active_cv(chunks, vectors)