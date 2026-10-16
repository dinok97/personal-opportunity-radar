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
            profile_row = (
                SimpleNamespace(document_id="cv-123", profile=self.profile_data)
                if self.profile_data is not None
                else None
            )
            return SimpleNamespace(
                scalar_one_or_none=lambda: self.profile_data,
                first=lambda: profile_row,
            )
        return None


def test_get_active_profile_returns_profile_for_document_id() -> None:
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


def test_get_first_active_profile_returns_first_profile_row() -> None:
    profile_data = {
        "full_name": "Ada Example",
        "professional_field": "Software Engineering",
        "target_roles": [{"name": "Machine Learning", "abbreviation": "ML"}],
        "technical_skills": ["Python", "PyTorch"],
    }
    session = FakeSession(profile_data)

    profile = CvProfileRepository().get_first_active_profile(session)

    assert profile == UserProfile.model_validate(profile_data)
    query = session.statements[1]
    assert query._limit_clause is not None
    assert query._order_by_clauses


def test_get_first_active_profile_returns_none_when_table_is_empty() -> None:
    session = FakeSession()

    profile = CvProfileRepository().get_first_active_profile(session)

    assert profile is None