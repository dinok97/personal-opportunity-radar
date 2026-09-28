from datetime import datetime, timezone

import pytest

from backend.app.services.cv_chunking import CvChunk, chunk_cv_pages
from backend.app.services.cv_pdf_extraction import ExtractedPdfPage


UPLOADED_AT = datetime(2026, 9, 27, 12, 0, tzinfo=timezone.utc)


def test_chunk_cv_pages_orders_pages_and_records_metadata() -> None:
    pages = [
        ExtractedPdfPage(page_number=2, text="Second page content"),
        ExtractedPdfPage(page_number=1, text="First page content"),
    ]

    chunks = chunk_cv_pages(
        pages,
        document_id="cv-123",
        filename="resume.pdf",
        uploaded_at=UPLOADED_AT,
        chunk_size=100,
        chunk_overlap=10,
    )

    assert [chunk.content for chunk in chunks] == ["First page content", "Second page content"]
    assert [chunk.metadata["page_number"] for chunk in chunks] == [1, 2]
    assert [chunk.metadata["chunk_index"] for chunk in chunks] == [0, 0]
    assert all(chunk.metadata["document_id"] == "cv-123" for chunk in chunks)
    assert all(chunk.metadata["filename"] == "resume.pdf" for chunk in chunks)
    assert all(chunk.metadata["uploaded_at"] == "2026-09-27T12:00:00+00:00" for chunk in chunks)


def test_chunk_cv_pages_handles_exact_boundaries_and_resets_chunk_indexes() -> None:
    chunks = chunk_cv_pages(
        [
            ExtractedPdfPage(page_number=2, text="uvwxyz"),
            ExtractedPdfPage(page_number=1, text="abcdefghijklmnopqrst"),
        ],
        document_id="cv-123",
        filename="resume.pdf",
        uploaded_at=UPLOADED_AT,
        chunk_size=10,
        chunk_overlap=2,
    )

    assert [chunk.content for chunk in chunks] == [
        "abcdefghij",
        "ijklmnopqr",
        "qrst",
        "uvwxyz",
    ]
    assert [
        (chunk.metadata["page_number"], chunk.metadata["chunk_index"])
        for chunk in chunks
    ] == [(1, 0), (1, 1), (1, 2), (2, 0)]


def test_chunk_cv_pages_creates_overlapping_chunks_at_word_boundaries() -> None:
    chunks = chunk_cv_pages(
        [ExtractedPdfPage(page_number=1, text="alpha beta gamma delta epsilon zeta")],
        document_id="cv-123",
        filename="resume.pdf",
        uploaded_at=UPLOADED_AT,
        chunk_size=17,
        chunk_overlap=6,
    )

    assert len(chunks) > 1
    assert chunks[0].content == "alpha beta gamma"
    assert chunks[1].content.startswith("beta gamma")
    assert all(len(chunk.content) <= 17 for chunk in chunks)


def test_chunk_cv_pages_advances_with_near_maximum_overlap() -> None:
    chunks = chunk_cv_pages(
        [ExtractedPdfPage(page_number=1, text="alpha beta gamma delta")],
        document_id="cv-123",
        filename="resume.pdf",
        uploaded_at=UPLOADED_AT,
        chunk_size=10,
        chunk_overlap=9,
    )

    assert len(chunks) > 1
    assert all(0 < len(chunk.content) <= 10 for chunk in chunks)


def test_chunk_cv_pages_skips_blank_pages_and_empty_documents() -> None:
    pages = [
        ExtractedPdfPage(page_number=1, text="  \n "),
        ExtractedPdfPage(page_number=2, text="A short CV"),
    ]

    chunks = chunk_cv_pages(
        pages,
        document_id="cv-123",
        filename="resume.pdf",
        uploaded_at=UPLOADED_AT,
    )

    assert [chunk.content for chunk in chunks] == ["A short CV"]
    assert chunks[0].metadata["page_number"] == 2
    assert chunk_cv_pages(
        [], document_id="cv-123", filename="resume.pdf", uploaded_at=UPLOADED_AT
    ) == []


def test_chunk_cv_pages_uses_stable_ids_for_retries() -> None:
    page = [ExtractedPdfPage(page_number=3, text="CV content that should retry safely")]
    options = {
        "document_id": "cv-123",
        "filename": "resume.pdf",
        "uploaded_at": UPLOADED_AT,
        "chunk_size": 12,
        "chunk_overlap": 3,
    }

    first_attempt = chunk_cv_pages(page, **options)
    retry = chunk_cv_pages(page, **options)

    assert [chunk.id for chunk in first_attempt] == [chunk.id for chunk in retry]
    assert all(isinstance(chunk, CvChunk) for chunk in first_attempt)


@pytest.mark.parametrize(
    ("options", "message"),
    [
        ({"document_id": ""}, "document_id"),
        ({"filename": " "}, "filename"),
        ({"chunk_size": 0}, "chunk_size"),
        ({"chunk_size": 10, "chunk_overlap": -1}, "chunk_overlap"),
        ({"chunk_size": 10, "chunk_overlap": 10}, "chunk_overlap"),
        ({"uploaded_at": datetime(2026, 9, 27)}, "uploaded_at"),
    ],
)
def test_chunk_cv_pages_rejects_invalid_inputs(options, message: str) -> None:
    parameters = {
        "document_id": "cv-123",
        "filename": "resume.pdf",
        "uploaded_at": UPLOADED_AT,
        "chunk_size": 100,
        "chunk_overlap": 10,
    }
    parameters.update(options)

    with pytest.raises(ValueError, match=message):
        chunk_cv_pages([ExtractedPdfPage(page_number=1, text="CV")], **parameters)