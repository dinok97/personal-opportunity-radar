from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import NAMESPACE_URL, uuid5

from .cv_pdf_extraction import ExtractedPdfPage

# section aware chunking for CVs
# put too much text in a single chunk and the embedding model will lose context
DEFAULT_CHUNK_SIZE = 400
DEFAULT_CHUNK_OVERLAP = 50


@dataclass(frozen=True)
class CvChunk:
    id: str
    content: str
    metadata: dict[str, str | int]


def _split_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    normalized_text = " ".join(text.split())
    chunks: list[str] = []
    start = 0

    while start < len(normalized_text):
        end = min(start + chunk_size, len(normalized_text))
        if end < len(normalized_text):
            minimum_end = start + max(chunk_size // 2, overlap + 1)
            boundary = normalized_text.rfind(" ", minimum_end, end)
            if boundary > start + overlap:
                end = boundary

        chunk = normalized_text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == len(normalized_text):
            break

        next_start = max(start + 1, end - overlap)
        if overlap:
            boundary = normalized_text.rfind(" ", start, next_start)
            if boundary >= start:
                next_start = boundary + 1
        start = next_start

    return chunks


def chunk_cv_pages(
    pages: list[ExtractedPdfPage],
    *,
    document_id: str,
    filename: str,
    uploaded_at: datetime | None = None,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[CvChunk]:
    if not document_id.strip():
        raise ValueError("document_id must not be empty")
    if not filename.strip():
        raise ValueError("filename must not be empty")
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be non-negative and smaller than chunk_size")

    upload_time = uploaded_at or datetime.now(timezone.utc)
    if upload_time.tzinfo is None or upload_time.utcoffset() is None:
        raise ValueError("uploaded_at must include a timezone")
    uploaded_at_value = upload_time.astimezone(timezone.utc).isoformat()

    chunks: list[CvChunk] = []
    for page in sorted(pages, key=lambda item: item.page_number):
        page_chunks = _split_text(page.text, chunk_size, chunk_overlap)
        for chunk_index, content in enumerate(page_chunks):
            stable_key = f"cv:{document_id}:{page.page_number}:{chunk_index}"
            chunks.append(
                CvChunk(
                    id=str(uuid5(NAMESPACE_URL, stable_key)),
                    content=content,
                    metadata={
                        "document_id": document_id,
                        "filename": filename,
                        "uploaded_at": uploaded_at_value,
                        "page_number": page.page_number,
                        "chunk_index": chunk_index,
                    },
                )
            )
    return chunks