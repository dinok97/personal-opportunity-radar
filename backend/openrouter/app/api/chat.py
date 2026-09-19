import json
import logging

from fastapi import APIRouter, HTTPException, Request, UploadFile
from pydantic import ValidationError

from ..config import get_settings
from ..models import ChatMessage, ChatRequest, ChatResponse
from ..openrouter import OpenRouterClient, OpenRouterError
from ..opportunities import find_opportunities

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")

MAX_PDF_BYTES = 10 * 1024 * 1024


def _job_context(jobs: list) -> str:
    return "\n".join(
        f"- {job.title} at {job.company}: {job.location}; {job.type}; skills: {', '.join(job.tags)}"
        for job in jobs
    )


def _parse_messages(raw_messages: str | None) -> list[ChatMessage]:
    if not raw_messages:
        return []
    try:
        payload = json.loads(raw_messages)
        return [ChatMessage.model_validate(message) for message in payload]
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail="messages must be a valid JSON array") from exc


async def _read_pdf_metadata(upload: UploadFile | None) -> str | None:
    if upload is None:
        return None

    file_name = upload.filename or "uploaded.pdf"
    is_pdf = upload.content_type == "application/pdf" or file_name.lower().endswith(".pdf")
    if not is_pdf:
        raise HTTPException(status_code=415, detail="Only PDF files are supported")

    content = await upload.read(MAX_PDF_BYTES + 1)
    if len(content) > MAX_PDF_BYTES:
        raise HTTPException(status_code=413, detail="PDF must be 10 MB or smaller")

    return file_name


@router.post("/chat", response_model=ChatResponse)
async def chat(request: Request) -> ChatResponse:
    content_type = request.headers.get("content-type", "")
    prompt = ""
    raw_messages: str | None = None
    file: UploadFile | None = None

    if "multipart/form-data" in content_type:
        form = await request.form()
        prompt = str(form.get("prompt") or "")
        raw_messages = str(form.get("messages")) if form.get("messages") else None
        form_file = form.get("file")
        if isinstance(form_file, UploadFile) or hasattr(form_file, "read"):
            file = form_file
    else:
        try:
            body = await request.json()
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Request body must be valid JSON") from exc
        try:
            request_data = ChatRequest.model_validate(body)
        except ValidationError as exc:
            raise HTTPException(status_code=400, detail="Invalid chat request") from exc
        prompt = request_data.prompt
        history = request_data.messages

    if "multipart/form-data" in content_type:
        history = _parse_messages(raw_messages)

    clean_prompt = prompt.strip()
    if not clean_prompt and not history and file is None:
        raise HTTPException(status_code=400, detail="prompt, messages, or a PDF file is required")

    file_name = await _read_pdf_metadata(file)
    jobs = find_opportunities(clean_prompt or "all")
    current_messages = [*history]
    if clean_prompt:
        current_messages.append(ChatMessage(role="user", content=clean_prompt))
    elif file_name:
        current_messages.append(
            ChatMessage(
                role="user",
                content="Review my uploaded CV and suggest relevant opportunities.",
            )
        )

    settings = get_settings()
    source = "demo"
    if settings.openrouter_api_key:
        try:
            message = await OpenRouterClient(settings).complete(
                current_messages,
                _job_context(jobs),
            )
            source = "openrouter"
        except OpenRouterError as exc:
            logger.warning("OpenRouter request failed: %s", exc)
            raise HTTPException(status_code=502, detail="The AI provider is unavailable") from exc
    else:
        message = (
            f"Demo mode is active. I found {len(jobs)} opportunities matching your profile. "
            "Add OPENROUTER_API_KEY to enable live responses."
        )

    if file_name:
        message = f"I received {file_name}. {message}"

    return ChatResponse(message=message, jobs=jobs, source=source, file_name=file_name)
