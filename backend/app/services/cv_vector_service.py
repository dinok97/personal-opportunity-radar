from collections.abc import Sequence

from ..config import Settings
from ..repositories.cv_vector_repository import (
    CvVectorDimensionError,
    CvVectorRepository,
)
from .embedding_service import EmbeddingClient, HuggingFaceEmbeddingClient
from .cv_chunking import CvChunk
from functools import lru_cache
from sentence_transformers import CrossEncoder

CV_RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def _get_reranker() -> CrossEncoder:
    return CrossEncoder(CV_RERANKER_MODEL)


class CvEmbeddingError(RuntimeError):
    """The configured model could not create embeddings for the CV chunks."""


class CvVectorService:
    def __init__(
        self,
        settings: Settings,
        *,
        repository: CvVectorRepository | None = None,
        embeddings: EmbeddingClient | None = None,
        reranker: CrossEncoder | None = None,
    ) -> None:
        self.embedding_dimension = settings.pgvector_embedding_dimension
        self.embeddings = embeddings or HuggingFaceEmbeddingClient(
            settings.embedding_model,
            settings.embedding_model_revision,
        )
        self.repository = repository or CvVectorRepository(settings, embeddings=self.embeddings)
        self.reranker = reranker

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


    def search(
        self,
        query: str,
        *,
        k: int = 5,
        candidate_k: int = 20,
    ):
        if not query.strip():
            raise ValueError("Query must not be empty")

        if k <= 0:
            raise ValueError("k must be greater than 0")

        if candidate_k < k:
            raise ValueError(
                "candidate_k must be greater than or equal to k"
            )

        # Stage 1: retrieve candidates from PGVector
        candidates = self.repository.search(
            query,
            k=candidate_k,
        )

        if not candidates:
            return []

        # Stage 2: rerank candidates
        reranker = self.reranker or _get_reranker()

        documents = [
            document.page_content
            for document in candidates
        ]

        ranked = reranker.rank(
            query,
            documents,
            top_k=min(k, len(documents)),
        )

        return [
            candidates[result["corpus_id"]]
            for result in ranked
        ]