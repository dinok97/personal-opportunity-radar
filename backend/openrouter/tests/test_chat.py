from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_demo_chat_returns_frontend_contract(monkeypatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    get_settings.cache_clear()

    response = client.post(
        "/api/chat",
        json={"prompt": "Find me remote ML jobs", "messages": []},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["source"] == "demo"
    assert payload["jobs"][0]["location"] == "Remote"
    assert payload["message"]


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
