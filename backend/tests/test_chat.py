import asyncio

import httpx
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from backend.app.config import Settings, get_settings
from backend.app.main import app
from backend.app.models import ChatMessage
from backend.app.ollama import OllamaClient, OllamaError
from backend.app.openrouter import OpenRouterClient


client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


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
