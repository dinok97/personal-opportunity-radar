from dataclasses import dataclass
from io import BytesIO

from pypdf import PdfReader
from pypdf.errors import PdfReadError


class CvPdfExtractionError(ValueError):
    """Base error for CV PDF parsing failures."""


class CvPdfMalformedError(CvPdfExtractionError):
    """The uploaded bytes could not be read as a PDF."""


class CvPdfEncryptedError(CvPdfExtractionError):
    """The PDF is encrypted and cannot be parsed without a password."""


class CvPdfEmptyError(CvPdfExtractionError):
    """The PDF is empty or contains no pages."""


class CvPdfNoTextError(CvPdfExtractionError):
    """The PDF has pages but no extractable text."""


@dataclass(frozen=True)
class ExtractedPdfPage:
    page_number: int
    text: str


def _normalize_text(text: str | None) -> str:
    if not text:
        return ""
    return "\n".join(
        " ".join(line.split())
        for line in text.replace("\r", "\n").splitlines()
        if line.strip()
    )


def extract_pdf_pages(content: bytes) -> list[ExtractedPdfPage]:
    if not content or not content.strip():
        raise CvPdfEmptyError("The PDF is empty")

    try:
        reader = PdfReader(BytesIO(content))
        if reader.is_encrypted:
            raise CvPdfEncryptedError("Encrypted PDFs are not supported")
        page_count = len(reader.pages)
        if page_count == 0:
            raise CvPdfEmptyError("The PDF contains no pages")

        pages = [
            ExtractedPdfPage(page_number=index, text=_normalize_text(page.extract_text()))
            for index, page in enumerate(reader.pages, start=1)
        ]
    except CvPdfExtractionError:
        raise
    except (PdfReadError, OSError, ValueError) as exc:
        raise CvPdfMalformedError("The uploaded file is not a readable PDF") from exc

    if not any(page.text for page in pages):
        raise CvPdfNoTextError("The PDF contains no extractable text")
    return pages