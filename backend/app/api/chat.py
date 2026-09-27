import json
import logging
from uuid import uuid4

import psycopg
from fastapi import APIRouter, HTTPException, Request, UploadFile
from pydantic import ValidationError

from ..config import get_settings
from ..models import ChatMessage, ChatRequest, ChatResponse
from ..ollama import OllamaClient, OllamaError
from ..openrouter import OpenRouterClient, OpenRouterError
from ..opportunities import find_opportunities
from ..repositories.cv_vector_repository import (
    CvVectorConfigurationError,
    CvVectorDimensionError,
    CvVectorSchemaError,
)
from ..services.cv_chunking import CvChunk, chunk_cv_pages
from ..services.cv_pdf_extraction import CvPdfExtractionError, extract_pdf_pages
from ..services.cv_vector_service import CvEmbeddingError, CvVectorService

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


async def _read_pdf(upload: UploadFile | None) -> tuple[str, bytes] | None:
    if upload is None:
        return None

    file_name = upload.filename or "uploaded.pdf"
    is_pdf = upload.content_type == "application/pdf" or file_name.lower().endswith(".pdf")
    if not is_pdf:
        raise HTTPException(status_code=415, detail="Only PDF files are supported")

    content = await upload.read(MAX_PDF_BYTES + 1)
    if len(content) > MAX_PDF_BYTES:
        raise HTTPException(status_code=413, detail="PDF must be 10 MB or smaller")

    return file_name, content


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

    pdf_upload = await _read_pdf(file)
    file_name = pdf_upload[0] if pdf_upload else None
    cv_chunks: list[CvChunk] = []
    document_id: str | None = None
    if pdf_upload:
        file_name, pdf_content = pdf_upload
        try:
            pages = extract_pdf_pages(pdf_content)
        except CvPdfExtractionError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

        document_id = str(uuid4())
        cv_chunks = chunk_cv_pages(
            pages,
            document_id=document_id,
            filename=file_name,
        )
        if not cv_chunks:
            raise HTTPException(status_code=422, detail="The PDF contains no text to store")

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
    if settings.llm_provider == "ollama":
        try:
            message = await OllamaClient(settings).complete(
                current_messages,
                _job_context(jobs),
            )
            source = "ollama"
        except OllamaError as exc:
            logger.warning("Ollama request failed: %s", exc)
            raise HTTPException(status_code=502, detail="The AI provider is unavailable") from exc
    elif settings.openrouter_api_key:
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

    if cv_chunks:
        try:
            CvVectorService(settings).replace_active_cv(cv_chunks)
        except (
            CvEmbeddingError,
            CvVectorConfigurationError,
            CvVectorDimensionError,
            CvVectorSchemaError,
            psycopg.Error,
        ) as exc:
            logger.exception("CV upload could not be persisted")
            raise HTTPException(
                status_code=503,
                detail="CV storage is unavailable",
            ) from exc

    if file_name:
        message = f"I received {file_name}. {message}"

    return ChatResponse(
        message=message,
        jobs=jobs,
        source=source,
        file_name=file_name,
        cv_uploaded=bool(cv_chunks),
        document_id=document_id if cv_chunks else None,
    )
