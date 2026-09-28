import json

import pytest

from backend.app.config import Settings
from backend.app.models import UserProfile
from backend.app.ollama import OllamaClient, OllamaError
from backend.app.services.cv_chunking import CvChunk
from backend.app.services.user_profile_service import (
    MAX_PROFILE_BATCH_CHARS,
    UserProfileExtractionError,
    UserProfileProviderError,
    UserProfileService,
)


def make_chunk(content: str, page_number: int = 1, chunk_index: int = 0) -> CvChunk:
    return CvChunk(
        id=f"chunk-{page_number}-{chunk_index}",
        content=content,
        metadata={"page_number": page_number, "chunk_index": chunk_index},
    )


def make_settings() -> Settings:
    return Settings(_env_file=None, llm_provider="ollama")


@pytest.mark.asyncio
async def test_extract_profile_batches_all_text_and_merges_supported_facts(monkeypatch) -> None:
    requests = []
    outputs = [
        {
            "name": "Alicia Morgan",
            "email": "alicia@example.com",
            "topSkills": ["Python", "SQL"],
            "profileSummary": "Experienced in applied machine learning.",
        },
        {
            "role": "ML Engineer",
            "topSkills": ["python", "NLP"],
            "interests": ["AI products"],
            "profileSummary": "Interested in research and AI products.",
        },
    ]

    async def extract_profile(self, cv_text):
        requests.append(cv_text)
        return json.dumps(outputs[len(requests) - 1])

    monkeypatch.setattr(OllamaClient, "extract_profile", extract_profile)
    chunks = [
        make_chunk("A" * MAX_PROFILE_BATCH_CHARS),
        make_chunk("Later CV content", page_number=2),
    ]

    profile = await UserProfileService(make_settings()).extract_profile(chunks)

    assert len(requests) == 2
    assert all(len(request) <= MAX_PROFILE_BATCH_CHARS for request in requests)
    assert "Later CV content" in "".join(requests)
    assert profile == UserProfile(
        name="Alicia Morgan",
        role="ML Engineer",
        email="alicia@example.com",
        topSkills=["Python", "SQL", "NLP"],
        interests=["AI products"],
        profileSummary=(
            "Experienced in applied machine learning.\n"
            "Interested in research and AI products."
        ),
    )


@pytest.mark.asyncio
async def test_extract_profile_defaults_unsupported_facts_to_empty_values(monkeypatch) -> None:
    async def extract_profile(self, cv_text):
        return '{"name":"Alicia"}'

    monkeypatch.setattr(OllamaClient, "extract_profile", extract_profile)

    profile = await UserProfileService(make_settings()).extract_profile([make_chunk("CV")])

    assert profile.name == "Alicia"
    assert profile.role == ""
    assert profile.topSkills == []
    assert profile.interests == []


@pytest.mark.asyncio
async def test_extract_profile_rejects_invalid_provider_json(monkeypatch) -> None:
    async def extract_profile(self, cv_text):
        return "not json"

    monkeypatch.setattr(OllamaClient, "extract_profile", extract_profile)

    with pytest.raises(UserProfileExtractionError):
        await UserProfileService(make_settings()).extract_profile([make_chunk("CV")])


@pytest.mark.asyncio
async def test_extract_profile_maps_provider_failure(monkeypatch) -> None:
    async def extract_profile(self, cv_text):
        raise OllamaError("provider unavailable")

    monkeypatch.setattr(OllamaClient, "extract_profile", extract_profile)

    with pytest.raises(UserProfileProviderError) as exc_info:
        await UserProfileService(make_settings()).extract_profile([make_chunk("CV")])

    assert isinstance(exc_info.value.__cause__, OllamaError)