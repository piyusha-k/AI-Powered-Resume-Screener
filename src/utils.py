"""Shared validation, logging, and text helpers."""

import csv
import logging
import re
import time
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Tuple

from config import EVALUATION_DIR, MAX_UPLOAD_BYTES

logger = logging.getLogger("resume_screener")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)


def get_upload_bytes(upload: Any) -> Tuple[str, bytes]:
    """Return a validated upload's filename and bytes."""
    name = Path(getattr(upload, "name", "")).name
    if not name or Path(name).suffix.lower() not in {".pdf", ".docx", ".txt"}:
        raise ValueError("Unsupported file type. Use PDF, DOCX, or TXT.")
    if hasattr(upload, "getvalue"):
        content = upload.getvalue()
    elif hasattr(upload, "read"):
        content = upload.read()
        if hasattr(upload, "seek"):
            upload.seek(0)
    else:
        raise ValueError("The uploaded file could not be read.")
    if not isinstance(content, bytes):
        raise ValueError("The uploaded file did not contain valid bytes.")
    if len(content) > MAX_UPLOAD_BYTES:
        raise ValueError("File exceeds the 10 MB upload limit.")
    if not content:
        raise ValueError("The uploaded file is empty.")
    return name, content


def append_processing_log(
    filename: str,
    duration_seconds: float,
    success: bool,
    skill_count: int,
    score: Optional[float] = None,
    error: Optional[str] = None,
) -> None:
    """Append minimal processing metadata; never persist extracted resume text."""
    EVALUATION_DIR.mkdir(parents=True, exist_ok=True)
    log_path = EVALUATION_DIR / "screening_log.csv"
    fields = [
        "timestamp_utc",
        "candidate_filename",
        "processing_seconds",
        "extraction_success",
        "extracted_skill_count",
        "final_score",
        "error",
    ]
    row = {
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "candidate_filename": Path(filename).name,
        "processing_seconds": round(duration_seconds, 3),
        "extraction_success": success,
        "extracted_skill_count": skill_count,
        "final_score": "" if score is None else round(score, 2),
        "error": (error or "")[:300],
    }
    try:
        needs_header = not log_path.exists()
        with log_path.open("a", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            if needs_header:
                writer.writeheader()
            writer.writerow(row)
    except OSError:
        logger.exception("Could not write processing log for %s", Path(filename).name)


def clean_text(text: str) -> str:
    """Normalize extracted document text while preserving technical punctuation."""
    text = text.replace("\x00", " ").replace("\u00a0", " ")
    text = re.sub(r"[\t\f\v ]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"(.)\1{5,}", r"\1\1\1", text)
    return text.strip()


def safe_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    """Convert a value to a finite float or return the supplied default."""
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    if result != result or result in (float("inf"), float("-inf")):
        return default
    return result

