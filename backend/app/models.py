from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str = Field(min_length=1, max_length=20_000)


class ChatRequest(BaseModel):
    prompt: str = Field(default="", max_length=20_000)
    messages: list[ChatMessage] = Field(default_factory=list, max_length=50)


class JobMatch(BaseModel):
    id: str
    title: str
    company: str
    location: str
    salary: str
    type: str
    matchScore: int
    description: str
    tags: list[str]
    reasons: list[str]
    missingSkills: list[str]
    source: str


class ChatResponse(BaseModel):
    message: str
    jobs: list[JobMatch] = Field(default_factory=list)
    source: Literal["openrouter", "ollama", "demo"]
    file_name: str | None = None
    cv_uploaded: bool = False
    document_id: str | None = None


class UserProfile(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = ""
    role: str = ""
    email: str = ""
    location: str = ""
    availability: str = ""
    topSkills: list[str] = Field(default_factory=list)
    interests: list[str] = Field(default_factory=list)
    profileSummary: str = ""
