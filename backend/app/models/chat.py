from typing import Literal

from pydantic import BaseModel, Field

from .job import JobSearchResult
from .profile import UserProfile


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str = Field(min_length=1, max_length=20_000)


class ChatRequest(BaseModel):
    prompt: str = Field(default="", max_length=20_000)
    messages: list[ChatMessage] = Field(default_factory=list, max_length=50)


class ChatResponse(BaseModel):
    message: str
    jobs: list[JobSearchResult] = Field(default_factory=list)
    source: Literal["openrouter", "ollama", "demo"]
    file_name: str | None = None
    cv_uploaded: bool = False
    document_id: str | None = None
    user_profile: UserProfile | None = None