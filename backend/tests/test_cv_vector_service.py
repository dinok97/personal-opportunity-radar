from datetime import datetime, timezone

import pytest

from backend.app.config import Settings
from backend.app.repositories.cv_vector_repository import CvVectorDimensionError
from backend.app.services.cv_chunking import CvChunk
from backend.app.services.cv_vector_service import CvEmbeddingError, CvVectorService


def make_chunk(chunk_id: str = "chunk-1", content: str = "CV text") -> CvChunk:
    return CvChunk(
        id=chunk_id,
        content=content,
        metadata={
            "document_id": "cv-1",
            "filename": "resume.pdf",
            "uploaded_at": datetime(2026, 9, 27, tzinfo=timezone.utc).isoformat(),
            "page_number": 1,
            "chunk_index": 0,
        },
    )


class FakeRepository:
    def __init__(self):
        self.setup_calls = 0
        self.replacement = None

    def setup(self) -> None:
        self.setup_calls += 1

    def replace_active_cv(self, chunks, embeddings) -> int:
        self.replacement = (chunks, embeddings)
        return len(chunks)


class FakeEmbeddings:
    def __init__(self, vectors=None, error: Exception | None = None):
        self.vectors = [[0.1, 0.2, 0.3]] if vectors is None else vectors
        self.error = error
        self.texts = None

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        self.texts = texts
        if self.error:
            raise self.error
        return self.vectors


def make_settings() -> Settings:
    return Settings(
        _env_file=None,
        pgvector_connection_string="postgresql://db/cv",
        pgvector_embedding_dimension=3,
        ollama_embedding_model="custom-embedding-model",
        ollama_embedding_base_url="http://ollama:11434",
    )


def test_cv_vector_service_embeds_then_replaces_active_cv() -> None:
    repository = FakeRepository()
    embeddings = FakeEmbeddings(vectors=[[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])
    chunks = [make_chunk("chunk-1", "First text"), make_chunk("chunk-2", "Second text")]
    service = CvVectorService(make_settings(), repository=repository, embeddings=embeddings)

    result = service.replace_active_cv(chunks)

    assert result == 2
    assert embeddings.texts == ["First text", "Second text"]
    assert repository.replacement == (chunks, embeddings.vectors)


def test_cv_vector_service_validates_dimension_before_repository_write() -> None:
    repository = FakeRepository()
    service = CvVectorService(
        make_settings(),
        repository=repository,
        embeddings=FakeEmbeddings(vectors=[[0.1, 0.2]]),
    )

    with pytest.raises(CvVectorDimensionError):
        service.replace_active_cv([make_chunk()])

    assert repository.replacement is None


def test_cv_vector_service_wraps_embedding_failures_before_repository_write() -> None:
    repository = FakeRepository()
    service = CvVectorService(
        make_settings(),
        repository=repository,
        embeddings=FakeEmbeddings(error=ConnectionError("Ollama unavailable")),
    )

    with pytest.raises(CvEmbeddingError) as exc_info:
        service.replace_active_cv([make_chunk()])

    assert isinstance(exc_info.value.__cause__, ConnectionError)
    assert repository.replacement is None


def test_cv_vector_service_rejects_missing_embedding_results() -> None:
    repository = FakeRepository()
    service = CvVectorService(
        make_settings(),
        repository=repository,
        embeddings=FakeEmbeddings(vectors=[]),
    )

    with pytest.raises(CvEmbeddingError, match="incomplete result"):
        service.replace_active_cv([make_chunk()])

    assert repository.replacement is None


def test_cv_vector_service_does_not_call_embedding_or_storage_for_empty_chunks() -> None:
    repository = FakeRepository()
    embeddings = FakeEmbeddings()
    service = CvVectorService(make_settings(), repository=repository, embeddings=embeddings)

    with pytest.raises(ValueError, match="At least one CV chunk"):
        service.replace_active_cv([])

    assert embeddings.texts is None
    assert repository.replacement is None


def test_cv_vector_service_uses_configured_embedding_model(monkeypatch) -> None:
    captured = {}

    class FakeOllamaEmbeddings:
        def __init__(self, *, model, base_url):
            captured.update(model=model, base_url=base_url)

    monkeypatch.setattr(
        "backend.app.services.cv_vector_service.OllamaEmbeddings",
        FakeOllamaEmbeddings,
    )

    CvVectorService(make_settings(), repository=FakeRepository())

    assert captured == {
        "model": "custom-embedding-model",
        "base_url": "http://ollama:11434",
    }