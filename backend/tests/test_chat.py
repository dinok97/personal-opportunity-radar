import asyncio
from types import SimpleNamespace

import httpx
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from backend.app.config import Settings, get_settings
from backend.app.main import app
from backend.app.models import ChatMessage
from backend.app.ollama import OllamaClient, OllamaError
from backend.app.openrouter import OpenRouterClient
from backend.app.repositories.cv_vector_repository import CvVectorConfigurationError
from backend.app.services.cv_chunking import CvChunk
from backend.app.services.cv_pdf_extraction import CvPdfMalformedError, ExtractedPdfPage
from backend.app.services.cv_vector_service import CvEmbeddingError


client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def mock_cv_ingestion(
    monkeypatch,
    *,
    extraction_error=None,
    storage_error=None,
    empty_chunks=False,
):
    captured = {}

    def extract_pdf(content: bytes):
        captured["pdf_content"] = content
        if extraction_error:
            raise extraction_error
        return [ExtractedPdfPage(page_number=1, text="Extracted CV text")]

    def chunk_pages(pages, *, document_id: str, filename: str):
        captured["document_id"] = document_id
        captured["filename"] = filename
        captured["pages"] = pages
        if empty_chunks:
            return []
        return [
            CvChunk(
                id="chunk-id",
                content=pages[0].text,
                metadata={"document_id": document_id, "filename": filename},
            )
        ]

    class FakeCvVectorService:
        def __init__(self, settings):
            captured["settings"] = settings

        def replace_active_cv(self, chunks):
            captured["chunks"] = chunks
            if storage_error:
                raise storage_error
            return len(chunks)

        # def search(self, query: str, *, k: int = 5):
        #     captured["search_query"] = query
        #     captured["search_k"] = k
        #     return []        

        def search(self, query: str, *, k: int = 5):
            captured["search_query"] = query
            captured["search_k"] = k

            return [
                SimpleNamespace(
                    page_content="I have experience in NLP and machine learning.",
                    metadata={
                        "document_id": "test-cv",
                        "page_number": 1,
                    },
                )
            ][:k]

    monkeypatch.setattr("backend.app.api.chat.extract_pdf_pages", extract_pdf)
    monkeypatch.setattr("backend.app.api.chat.chunk_cv_pages", chunk_pages)
    monkeypatch.setattr("backend.app.api.chat.CvVectorService", FakeCvVectorService)
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    return captured


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_demo_chat_returns_frontend_contract(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "")

    response = client.post(
        "/api/chat",
        json={"prompt": "Find me remote ML jobs", "messages": []},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["source"] == "demo"
    assert payload["jobs"][0]["location"] == "Remote"
    assert payload["message"]


def test_openrouter_chat_uses_selected_provider(monkeypatch) -> None:
    async def complete(self, messages, job_context):
        return "OpenRouter response"

    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr(OpenRouterClient, "complete", complete)

    response = client.post("/api/chat", json={"prompt": "Find AI roles"})

    assert response.status_code == 200
    assert response.json()["message"] == "OpenRouter response"
    assert response.json()["source"] == "openrouter"


def test_ollama_chat_works_without_openrouter_key(monkeypatch) -> None:
    async def complete(self, messages, job_context):
        return "Ollama response"

    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    monkeypatch.setattr(OllamaClient, "complete", complete)

    response = client.post("/api/chat", json={"prompt": "Find AI roles"})

    assert response.status_code == 200
    assert response.json()["message"] == "Ollama response"
    assert response.json()["source"] == "ollama"


def test_ollama_completion_uses_openai_compatible_endpoint(monkeypatch) -> None:
    captured = {}

    class FakeAsyncClient:
        def __init__(self, timeout):
            captured["timeout"] = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, traceback):
            return None

        async def post(self, endpoint, headers, json):
            captured.update(endpoint=endpoint, headers=headers, payload=json)
            return httpx.Response(
                200,
                json={"choices": [{"message": {"content": "  Local answer  "}}]},
            )

    monkeypatch.setattr("backend.app.ollama.httpx.AsyncClient", FakeAsyncClient)
    settings = Settings(
        llm_provider="ollama",
        ollama_base_url="http://ollama:11434/v1/",
        ollama_model="test-model",
    )

    result = asyncio.run(
        OllamaClient(settings).complete(
            [ChatMessage(role="user", content="Find jobs")],
            "Relevant job context",
        )
    )

    assert result == "Local answer"
    assert captured["endpoint"] == "http://ollama:11434/v1/chat/completions"
    assert captured["payload"]["model"] == "test-model"
    assert captured["payload"]["stream"] is False
    assert captured["payload"]["messages"][-1] == {"role": "user", "content": "Find jobs"}
    assert "Relevant job context" in captured["payload"]["messages"][0]["content"]
    assert "Authorization" not in captured["headers"]


def test_ollama_failure_returns_bad_gateway(monkeypatch) -> None:
    async def fail(self, messages, job_context):
        raise OllamaError("Ollama is unavailable")

    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.setattr(OllamaClient, "complete", fail)

    response = client.post("/api/chat", json={"prompt": "Find AI roles"})

    assert response.status_code == 502
    assert response.json()["detail"] == "The AI provider is unavailable"


def test_invalid_llm_provider_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Settings(llm_provider="unsupported")


def test_cv_vector_settings_have_independent_defaults() -> None:
    settings = Settings(_env_file=None)

    assert settings.embedding_model == "jinaai/jina-embeddings-v5-text-nano"
    assert settings.embedding_model_revision == "8a7f00a"
    assert settings.pgvector_connection_string is None
    assert settings.pgvector_collection_name == "cv_chunks"
    assert settings.pgvector_embedding_dimension == 768


def test_cv_vector_settings_can_be_overridden_by_environment(monkeypatch) -> None:
    monkeypatch.setenv("EMBEDDING_MODEL", "custom-embedder")
    monkeypatch.setenv("EMBEDDING_MODEL_REVISION", "custom-revision")
    monkeypatch.setenv("PGVECTOR_CONNECTION_STRING", "postgresql://db/cv")
    monkeypatch.setenv("PGVECTOR_COLLECTION_NAME", "candidate_cv_chunks")
    monkeypatch.setenv("PGVECTOR_EMBEDDING_DIMENSION", "1024")

    settings = Settings(_env_file=None)

    assert settings.embedding_model == "custom-embedder"
    assert settings.embedding_model_revision == "custom-revision"
    assert settings.pgvector_connection_string == "postgresql://db/cv"
    assert settings.pgvector_collection_name == "candidate_cv_chunks"
    assert settings.pgvector_embedding_dimension == 1024


@pytest.mark.parametrize(
    "settings_kwargs",
    [
        {"pgvector_embedding_dimension": 0},
        {"pgvector_collection_name": "cv-chunks"},
        {"pgvector_collection_name": "1cv_chunks"},
        {"pgvector_connection_string": ""},
    ],
)
def test_invalid_cv_vector_settings_are_rejected(settings_kwargs) -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **settings_kwargs)


def test_empty_chat_request_is_rejected() -> None:
    response = client.post("/api/chat", json={"prompt": "", "messages": []})

    assert response.status_code == 400
    assert response.json()["detail"] == "prompt, messages, or a PDF file is required"


def test_non_pdf_upload_is_rejected() -> None:
    response = client.post(
        "/api/chat",
        data={"prompt": "Review this"},
        files={"file": ("resume.txt", b"not a pdf", "text/plain")},
    )

    assert response.status_code == 415
    assert response.json()["detail"] == "Only PDF files are supported"


def test_pdf_upload_is_extracted_persisted_and_returns_document_id(monkeypatch) -> None:
    captured = mock_cv_ingestion(monkeypatch)

    response = client.post(
        "/api/chat",
        data={"prompt": "Review this CV"},
        files={"file": ("resume.pdf", b"pdf bytes", "application/pdf")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["file_name"] == "resume.pdf"
    assert payload["cv_uploaded"] is True
    assert payload["document_id"] == captured["document_id"]
    assert payload["message"].startswith("I received resume.pdf.")
    assert captured["pdf_content"] == b"pdf bytes"
    assert captured["chunks"][0].metadata["document_id"] == payload["document_id"]


def test_chat_includes_retrieved_cv_context(monkeypatch) -> None:
    captured = mock_cv_ingestion(monkeypatch)

    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    llm_context = {}

    async def fake_complete(self, messages, job_context):
        llm_context["job_context"] = job_context
        return "Mock answer"

    monkeypatch.setattr(
        "backend.app.api.chat.OpenRouterClient.complete",
        fake_complete,
    )

    response = client.post(
        "/api/chat",
        data={"prompt": "What experience do I have in NLP?"},
        files={"file": ("resume.pdf", b"pdf bytes", "application/pdf")},
    )

    assert response.status_code == 200

    assert "CV CONTEXT:" in llm_context["job_context"]
    assert (
        "I have experience in NLP and machine learning."
        in llm_context["job_context"]
    )

    assert captured["search_query"] == "What experience do I have in NLP?"
    assert captured["search_k"] == 5


def test_chat_retrieves_existing_cv_without_new_upload(monkeypatch) -> None:
    captured = {}

    class FakeCvVectorService:
        def __init__(self, settings):
            captured["settings"] = settings

        def search(self, query: str, *, k: int = 5):
            captured["search_query"] = query
            captured["search_k"] = k

            return [
                SimpleNamespace(
                    page_content="I have experience in NLP and machine learning.",
                    metadata={
                        "document_id": "existing-cv",
                        "page_number": 1,
                    },
                )
            ][:k]

    monkeypatch.setattr(
        "backend.app.api.chat.CvVectorService",
        FakeCvVectorService,
    )

    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv(
        "PGVECTOR_CONNECTION_STRING",
        "postgresql://test-user:test-password@localhost:5432/test-db",
    )

    llm_context = {}

    async def fake_complete(self, messages, job_context):
        llm_context["job_context"] = job_context
        return "Mock answer"

    monkeypatch.setattr(
        "backend.app.api.chat.OpenRouterClient.complete",
        fake_complete,
    )

    response = client.post(
        "/api/chat",
        json={"prompt": "What experience do I have in NLP?"},
    )

    assert response.status_code == 200

    assert "CV CONTEXT:" in llm_context["job_context"]
    assert (
        "I have experience in NLP and machine learning."
        in llm_context["job_context"]
    )

    assert captured["search_query"] == "What experience do I have in NLP?"
    assert captured["search_k"] == 5

def test_unreadable_pdf_returns_unprocessable_entity(monkeypatch) -> None:
    captured = mock_cv_ingestion(
        monkeypatch,
        extraction_error=CvPdfMalformedError("The uploaded file is not a readable PDF"),
    )

    response = client.post(
        "/api/chat",
        data={"prompt": "Review this CV"},
        files={"file": ("resume.pdf", b"invalid", "application/pdf")},
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "The uploaded file is not a readable PDF"
    assert "chunks" not in captured


def test_pdf_with_no_chunks_is_not_reported_as_uploaded(monkeypatch) -> None:
    captured = mock_cv_ingestion(monkeypatch, empty_chunks=True)

    response = client.post(
        "/api/chat",
        data={"prompt": "Review this CV"},
        files={"file": ("resume.pdf", b"pdf bytes", "application/pdf")},
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "The PDF contains no text to store"
    assert "chunks" not in captured


def test_oversized_pdf_is_rejected(monkeypatch) -> None:
    monkeypatch.setattr("backend.app.api.chat.MAX_PDF_BYTES", 2)

    response = client.post(
        "/api/chat",
        data={"prompt": "Review this CV"},
        files={"file": ("resume.pdf", b"123", "application/pdf")},
    )

    assert response.status_code == 413
    assert response.json()["detail"] == "PDF must be 10 MB or smaller"


@pytest.mark.parametrize(
    "storage_error",
    [
        CvEmbeddingError("Ollama unavailable"),
        CvVectorConfigurationError("PGVECTOR_CONNECTION_STRING is not configured"),
            SQLAlchemyError("database unavailable"),
    ],
)
def test_cv_storage_failure_does_not_report_upload_success(monkeypatch, storage_error) -> None:
    mock_cv_ingestion(monkeypatch, storage_error=storage_error)

    response = client.post(
        "/api/chat",
        data={"prompt": "Review this CV"},
        files={"file": ("resume.pdf", b"pdf bytes", "application/pdf")},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "CV storage is unavailable"
