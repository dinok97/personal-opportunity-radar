from collections.abc import Sequence

from ..config import Settings
from ..repositories.cv_vector_repository import (
    CvVectorDimensionError,
    CvVectorRepository,
)
from .embedding_service import EmbeddingClient, HuggingFaceEmbeddingClient
from .cv_chunking import CvChunk


class CvEmbeddingError(RuntimeError):
    """The configured model could not create embeddings for the CV chunks."""


class CvVectorService:
    def __init__(
        self,
        settings: Settings,
        *,
        repository: CvVectorRepository | None = None,
        embeddings: EmbeddingClient | None = None,
    ) -> None:
        self.embedding_dimension = settings.pgvector_embedding_dimension
        self.embeddings = embeddings or HuggingFaceEmbeddingClient(
            settings.embedding_model,
            settings.embedding_model_revision,
        )
        self.repository = repository or CvVectorRepository(settings, embeddings=self.embeddings)

    def setup(self) -> None:
        self.repository.setup()

    def replace_active_cv(self, chunks: Sequence[CvChunk]) -> int:
        if not chunks:
            raise ValueError("At least one CV chunk is required")

        try:
            print("Generating embeddings for CV chunks...")
            vectors = self.embeddings.embed_documents([chunk.content for chunk in chunks])
            print(f"Generated {len(vectors)} embeddings for {len(chunks)} CV chunks.")
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


    def search(self, query: str, *, k: int = 5):
        if not query.strip():
            raise ValueError("Query must not be empty")

        return self.repository.search(query, k=k)