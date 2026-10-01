import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from backend.app.config import get_settings
from backend.app.main import app
from backend.app.models import UserProfile
from backend.app.services.cv_chunking import CvChunk
from backend.app.services.user_profile_service import (
    UserProfileExtractionError,
    UserProfileProviderError,
)


client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def mock_user_api(monkeypatch, *, chunks=None, repository_error=None, service_error=None):
    captured = {}

    class FakeRepository:
        def __init__(self, settings):
            self.profile = None

        def get_active_cv_chunks(self):
            if repository_error:
                raise repository_error
            return chunks or []

        def save_user_profile(self, profile):
            self.profile = profile
            captured["saved_profile"] = profile

    class FakeProfileService:
        def __init__(self, settings):
            pass

        async def extract_profile(self, current_chunks):
            if service_error:
                raise service_error
            return UserProfile(
                name="Alicia Morgan",
                role="ML Engineer",
                topSkills=["Python", "NLP"],
            )

    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.setenv("PGVECTOR_CONNECTION_STRING", "postgresql://db/cv")
    monkeypatch.setattr("backend.app.api.user.CvVectorRepository", FakeRepository)
    monkeypatch.setattr("backend.app.api.user.UserProfileService", FakeProfileService)
    return captured


def test_get_user_returns_profile_contract(monkeypatch) -> None:
    captured = mock_user_api(
        monkeypatch,
        chunks=[CvChunk(id="id", content="CV", metadata={})],
    )

    response = client.get("/api/user")

    assert response.status_code == 200
    assert response.json() == {
        "name": "Alicia Morgan",
        "role": "ML Engineer",
        "email": "",
        "location": "",
        "availability": "",
        "topSkills": ["Python", "NLP"],
        "interests": [],
        "profileSummary": "",
    }
    assert captured["saved_profile"].name == "Alicia Morgan"


def test_get_user_returns_not_found_without_active_cv(monkeypatch) -> None:
    mock_user_api(monkeypatch)

    response = client.get("/api/user")

    assert response.status_code == 404
    assert response.json()["detail"] == "No CV has been uploaded"


def test_get_user_returns_service_unavailable_for_storage_failure(monkeypatch) -> None:
    mock_user_api(monkeypatch, repository_error=SQLAlchemyError("database unavailable"))

    response = client.get("/api/user")

    assert response.status_code == 503
    assert response.json()["detail"] == "CV storage is unavailable"


@pytest.mark.parametrize(
    ("service_error", "status_code", "detail"),
    [
        (UserProfileProviderError("provider unavailable"), 503, "Profile extraction is unavailable"),
        (
            UserProfileExtractionError("invalid provider output"),
            502,
            "The AI provider returned an invalid profile",
        ),
    ],
)
def test_get_user_maps_profile_extraction_failures(
    monkeypatch, service_error, status_code, detail
) -> None:
    mock_user_api(
        monkeypatch,
        chunks=[CvChunk(id="id", content="CV", metadata={})],
        service_error=service_error,
    )

    response = client.get("/api/user")

    assert response.status_code == status_code
    assert response.json()["detail"] == detail