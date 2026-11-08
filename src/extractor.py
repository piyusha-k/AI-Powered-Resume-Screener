"""PDF, DOCX, and text extraction with OCR fallback for scanned PDFs."""

import io
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from config import MIN_PDF_TEXT_CHARACTERS, SUPPORTED_JOB_TYPES, SUPPORTED_RESUME_TYPES
from src.preprocessor import detect_sections
from src.utils import clean_text

logger = logging.getLogger("resume_screener")


def _read_docx(content: bytes) -> str:
    try:
        from docx import Document
    except ImportError as exc:
        raise RuntimeError("DOCX support requires python-docx; install requirements.txt.") from exc
    document = Document(io.BytesIO(content))
    paragraphs = [paragraph.text for paragraph in document.paragraphs if paragraph.text.strip()]
    for table in document.tables:
        for row in table.rows:
            paragraphs.append(" | ".join(cell.text for cell in row.cells))
    return "\n".join(paragraphs)


def _read_pdf(content: bytes, enable_ocr: bool) -> Tuple[str, str]:
    try:
        from pypdf import PdfReader
    except ImportError:
        try:
            from PyPDF2 import PdfReader
        except ImportError as exc:
            raise RuntimeError("PDF support requires pypdf; install requirements.txt.") from exc
    reader = PdfReader(io.BytesIO(content))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    method = "text"
    if len(clean_text(text)) < MIN_PDF_TEXT_CHARACTERS and enable_ocr:
        try:
            from pdf2image import convert_from_bytes
            import pytesseract
        except ImportError:
            logger.warning("PDF text is sparse and OCR dependencies are unavailable.")
        else:
            try:
                pages = convert_from_bytes(content, first_page=1, last_page=min(len(reader.pages), 10))
                ocr_text = "\n".join(pytesseract.image_to_string(page) for page in pages)
                if len(clean_text(ocr_text)) > len(clean_text(text)):
                    text, method = ocr_text, "ocr"
            except Exception:
                logger.exception("OCR failed while processing a scanned PDF.")
                raise RuntimeError("PDF text extraction was insufficient and OCR failed.")
    return clean_text(text), method


def extract_document(
    filename: str,
    content: bytes,
    *,
    document_kind: str = "resume",
    enable_ocr: bool = True,
) -> Dict[str, Any]:
    """Extract a supported document and reject unreadable resumes explicitly."""
    suffix = Path(filename).suffix.lower()
    allowed = SUPPORTED_JOB_TYPES if document_kind == "job" else SUPPORTED_RESUME_TYPES
    if suffix not in allowed:
        raise ValueError("Unsupported file type for this document.")
    if not content:
        raise ValueError("The document is empty.")
    if suffix == ".pdf":
        text, method = _read_pdf(content, enable_ocr)
    elif suffix == ".docx":
        text, method = clean_text(_read_docx(content)), "docx"
    else:
        text, method = clean_text(content.decode("utf-8-sig", errors="replace")), "text"
    if len(text.strip()) < 20:
        raise ValueError("No readable text was extracted; this document cannot be scored.")
    return {
        "filename": Path(filename).name,
        "text": text,
        "sections": detect_sections(text),
        "extraction_method": method,
    }


def extract_file(path: Path, *, document_kind: str = "resume", enable_ocr: bool = True) -> Dict[str, Any]:
    """Read and extract a local file."""
    try:
        content = path.read_bytes()
    except OSError as exc:
        raise ValueError("The document could not be read.") from exc
    return extract_document(
        path.name, content, document_kind=document_kind, enable_ocr=enable_ocr
    )

