from io import BytesIO

import pytest
from pypdf import PdfWriter
from pypdf.errors import PdfReadError

from backend.app.services import cv_pdf_extraction
from backend.app.services.cv_pdf_extraction import (
    CvPdfEmptyError,
    CvPdfEncryptedError,
    CvPdfMalformedError,
    CvPdfNoTextError,
    ExtractedPdfPage,
    extract_pdf_pages,
)


class FakePage:
    def __init__(self, text: str | None):
        self.text = text

    def extract_text(self) -> str | None:
        return self.text


class FakeReader:
    def __init__(self, content: BytesIO):
        self.is_encrypted = False
        self.pages = [FakePage("  First   page\nline two "), FakePage("Second page")]


def make_text_pdf(page_texts: list[str]) -> bytes:
    objects = {
        1: b"<< /Type /Catalog /Pages 2 0 R >>",
        3: b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    }
    page_ids = [4 + 2 * index for index in range(len(page_texts))]
    page_references = " ".join(f"{page_id} 0 R" for page_id in page_ids)
    objects[2] = (
        f"<< /Type /Pages /Kids [{page_references}] /Count {len(page_ids)} >>".encode()
    )

    for page_id, text in zip(page_ids, page_texts):
        stream = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode()
        stream_id = page_id + 1
        objects[page_id] = (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Resources << /Font << /F1 3 0 R >> >> /Contents {stream_id} 0 R >>"
        ).encode()
        objects[stream_id] = f"<< /Length {len(stream)} >>\nstream\n".encode() + stream + b"\nendstream"

    data = bytearray(b"%PDF-1.4\n")
    offsets = [0] * (max(objects) + 1)
    for object_id, value in sorted(objects.items()):
        offsets[object_id] = len(data)
        data.extend(f"{object_id} 0 obj\n".encode() + value + b"\nendobj\n")

    xref_offset = len(data)
    data.extend(f"xref\n0 {len(offsets)}\n".encode())
    data.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        data.extend(f"{offset:010d} 00000 n \n".encode())
    data.extend(
        f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF".encode()
    )
    return bytes(data)


def test_extract_pdf_pages_preserves_page_numbers_and_normalizes_text(monkeypatch) -> None:
    monkeypatch.setattr(cv_pdf_extraction, "PdfReader", FakeReader)

    pages = extract_pdf_pages(b"pdf bytes")

    assert pages == [
        ExtractedPdfPage(page_number=1, text="First page\nline two"),
        ExtractedPdfPage(page_number=2, text="Second page"),
    ]


def test_extract_pdf_pages_extracts_text_from_real_multi_page_pdf() -> None:
    pages = extract_pdf_pages(make_text_pdf(["First page", "Second page"]))

    assert pages == [
        ExtractedPdfPage(page_number=1, text="First page"),
        ExtractedPdfPage(page_number=2, text="Second page"),
    ]


def test_extract_pdf_pages_keeps_blank_pages_in_page_sequence(monkeypatch) -> None:
    class ReaderWithBlankPage(FakeReader):
        def __init__(self, content: BytesIO):
            self.is_encrypted = False
            self.pages = [FakePage("Page one"), FakePage(None), FakePage("Page three")]

    monkeypatch.setattr(cv_pdf_extraction, "PdfReader", ReaderWithBlankPage)

    pages = extract_pdf_pages(b"pdf bytes")

    assert [page.page_number for page in pages] == [1, 2, 3]
    assert [page.text for page in pages] == ["Page one", "", "Page three"]


@pytest.mark.parametrize("content", [b"", b"   "])
def test_extract_pdf_pages_rejects_empty_content(content: bytes) -> None:
    with pytest.raises(CvPdfEmptyError):
        extract_pdf_pages(content)


def test_extract_pdf_pages_rejects_pdf_without_pages(monkeypatch) -> None:
    class EmptyReader:
        def __init__(self, content: BytesIO):
            self.is_encrypted = False
            self.pages = []

    monkeypatch.setattr(cv_pdf_extraction, "PdfReader", EmptyReader)

    with pytest.raises(CvPdfEmptyError):
        extract_pdf_pages(b"pdf bytes")


def test_extract_pdf_pages_rejects_encrypted_pdf(monkeypatch) -> None:
    class EncryptedReader(FakeReader):
        def __init__(self, content: BytesIO):
            self.is_encrypted = True
            self.pages = []

    monkeypatch.setattr(cv_pdf_extraction, "PdfReader", EncryptedReader)

    with pytest.raises(CvPdfEncryptedError):
        extract_pdf_pages(b"pdf bytes")


def test_extract_pdf_pages_rejects_pdf_without_extractable_text(monkeypatch) -> None:
    class TextlessReader(FakeReader):
        def __init__(self, content: BytesIO):
            self.is_encrypted = False
            self.pages = [FakePage(None), FakePage("  \n ")]

    monkeypatch.setattr(cv_pdf_extraction, "PdfReader", TextlessReader)

    with pytest.raises(CvPdfNoTextError):
        extract_pdf_pages(b"pdf bytes")


def test_extract_pdf_pages_maps_parser_errors_to_malformed(monkeypatch) -> None:
    def fail_to_read(content: BytesIO):
        raise PdfReadError("not a PDF")

    monkeypatch.setattr(cv_pdf_extraction, "PdfReader", fail_to_read)

    with pytest.raises(CvPdfMalformedError):
        extract_pdf_pages(b"not a PDF")


def test_extract_pdf_pages_rejects_malformed_pdf_bytes() -> None:
    with pytest.raises(CvPdfMalformedError):
        extract_pdf_pages(b"not a PDF")


def test_extract_pdf_pages_rejects_generated_blank_pdf() -> None:
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    content = BytesIO()
    writer.write(content)

    with pytest.raises(CvPdfNoTextError):
        extract_pdf_pages(content.getvalue())