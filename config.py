"""Application configuration and project paths."""

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
JOB_DESCRIPTIONS_DIR = DATA_DIR / "job_descriptions"
SAMPLE_RESUMES_DIR = DATA_DIR / "sample_resumes"
EVALUATION_DIR = DATA_DIR / "evaluation"
REPORTS_DIR = PROJECT_ROOT / "reports"

DEFAULT_SCORING_WEIGHTS = {
    "skills": 50.0,
    "experience": 30.0,
    "education_certifications": 10.0,
    "keyword_coverage": 10.0,
}
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MIN_PDF_TEXT_CHARACTERS = 80
SPACY_MODEL = os.getenv("SPACY_MODEL", "en_core_web_sm")
SEMANTIC_MODEL = os.getenv("SEMANTIC_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
SUPPORTED_RESUME_TYPES = {".pdf", ".docx"}
SUPPORTED_JOB_TYPES = {".txt", ".pdf", ".docx"}
