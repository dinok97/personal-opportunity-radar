from collections.abc import Sequence

from pydantic import ValidationError

from ..config import Settings
from ..models import UserProfile
from ..ollama import OllamaClient, OllamaError
from ..openrouter import OpenRouterClient, OpenRouterError
from .cv_chunking import CvChunk

MAX_PROFILE_BATCH_CHARS = 12_000


class UserProfileProviderError(RuntimeError):
    """The configured LLM provider could not extract a profile."""


class UserProfileExtractionError(RuntimeError):
    """The LLM returned a profile that could not be validated."""


def _batch_cv_text(chunks: Sequence[CvChunk]) -> list[str]:
    batches: list[str] = []
    current_parts: list[str] = []
    current_length = 0

    for chunk in chunks:
        prefix = (
            f"[page {chunk.metadata.get('page_number', '')}, "
            f"chunk {chunk.metadata.get('chunk_index', '')}]\n"
        )
        text = f"{prefix}{chunk.content}\n"
        for offset in range(0, len(text), MAX_PROFILE_BATCH_CHARS):
            part = text[offset : offset + MAX_PROFILE_BATCH_CHARS]
            if current_length + len(part) > MAX_PROFILE_BATCH_CHARS:
                batches.append("".join(current_parts))
                current_parts = []
                current_length = 0
            current_parts.append(part)
            current_length += len(part)

    if current_parts:
        batches.append("".join(current_parts))
    return batches


def _merge_profiles(profiles: Sequence[UserProfile]) -> UserProfile:
    def first_value(field: str) -> str:
        return next((getattr(profile, field) for profile in profiles if getattr(profile, field)), "")

    def merged_values(field: str) -> list[str]:
        values: list[str] = []
        seen: set[str] = set()
        for profile in profiles:
            for value in getattr(profile, field):
                normalized = value.casefold()
                if normalized not in seen:
                    seen.add(normalized)
                    values.append(value)
        return values

    summaries: list[str] = []
    for profile in profiles:
        if profile.profileSummary and profile.profileSummary not in summaries:
            summaries.append(profile.profileSummary)

    return UserProfile(
        name=first_value("name"),
        role=first_value("role"),
        email=first_value("email"),
        location=first_value("location"),
        availability=first_value("availability"),
        topSkills=merged_values("topSkills"),
        interests=merged_values("interests"),
        profileSummary="\n".join(summaries),
    )


class UserProfileService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def extract_profile(self, chunks: Sequence[CvChunk]) -> UserProfile:
        if not chunks:
            raise ValueError("At least one CV chunk is required")

        if self.settings.llm_provider == "ollama":
            provider = OllamaClient(self.settings)
            provider_errors = (OllamaError,)
        else:
            provider = OpenRouterClient(self.settings)
            provider_errors = (OpenRouterError,)

        profiles: list[UserProfile] = []
        for batch in _batch_cv_text(chunks):
            try:
                response = await provider.extract_profile(batch)
            except provider_errors as exc:
                raise UserProfileProviderError("The configured AI provider is unavailable") from exc

            try:
                profiles.append(UserProfile.model_validate_json(response))
            except (ValidationError, ValueError) as exc:
                raise UserProfileExtractionError(
                    "The AI provider returned an invalid profile"
                ) from exc

        return _merge_profiles(profiles)