from types import SimpleNamespace

from sqlalchemy.sql import Select

from backend.app.models import UserProfile
from backend.app.repositories.cv_profile_repository import CvProfileRepository


class FakeSession:
    def __init__(self, profile_data=None):
        self.profile_data = profile_data
        self.statements = []

    def execute(self, statement):
        self.statements.append(statement)
        if isinstance(statement, Select):
            return SimpleNamespace(scalar_one_or_none=lambda: self.profile_data)
        return None


def test_get_active_profile_returns_validated_profile_for_document_id() -> None:
    profile_data = {
        "full_name": "Ada Example",
        "professional_field": "Software Engineering",
        "target_roles": [
            {"name": "Machine Learning", "abbreviation": "ML"},
        ],
        "technical_skills": ["Python", "PyTorch"],
    }
    session = FakeSession(profile_data)

    profile = CvProfileRepository().get_active_profile(session, "cv-123")

    assert profile == UserProfile.model_validate(profile_data)
    assert len(session.statements) == 2
    query = session.statements[1]
    assert query.compile().params["document_id_1"] == "cv-123"


def test_get_active_profile_returns_none_when_document_has_no_profile() -> None:
    session = FakeSession()

    profile = CvProfileRepository().get_active_profile(session, "missing-cv")

    assert profile is None
    assert len(session.statements) == 2