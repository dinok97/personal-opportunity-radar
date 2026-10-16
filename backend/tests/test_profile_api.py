from contextlib import nullcontext
from types import SimpleNamespace

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.models import UserProfile

client = TestClient(app)


def test_get_profile_returns_active_profile(monkeypatch) -> None:
    profile = UserProfile(
        full_name="Ada Example",
        professional_field="Software Engineering",
        target_roles=[{"name": "Machine Learning", "abbreviation": "ML"}],
        technical_skills=["Python", "PyTorch"],
    )

    class FakeRepository:
        def get_active_profile(self, session, document_id):
            assert document_id == "cv-123"
            return profile

    class FakeCvVectorService:
        def __init__(self, settings):
            self.repository = SimpleNamespace(
                vector_store=SimpleNamespace(session_maker=lambda: nullcontext())
            )

    monkeypatch.setattr("backend.app.api.profile.CvVectorService", FakeCvVectorService)
    monkeypatch.setattr("backend.app.api.profile.CvProfileRepository", FakeRepository)

    response = client.get("/api/profile/cv-123")

    assert response.status_code == 200
    assert response.json() == profile.model_dump(mode="json")


def test_get_profile_returns_404_when_profile_does_not_exist(monkeypatch) -> None:
    class FakeRepository:
        def get_active_profile(self, session, document_id):
            assert document_id == "missing-cv"
            return None

    class FakeCvVectorService:
        def __init__(self, settings):
            self.repository = SimpleNamespace(
                vector_store=SimpleNamespace(session_maker=lambda: nullcontext())
            )

    monkeypatch.setattr("backend.app.api.profile.CvVectorService", FakeCvVectorService)
    monkeypatch.setattr("backend.app.api.profile.CvProfileRepository", FakeRepository)

    response = client.get("/api/profile/missing-cv")

    assert response.status_code == 404
    assert response.json() == {"detail": "Profile not found"}