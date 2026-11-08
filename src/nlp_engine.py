"""Rule-based resume/JD extraction with optional spaCy enhancement."""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence

from config import SPACY_MODEL
from src.taxonomy import extract_skills

_SPACY_PIPELINES = {}


def _get_spacy_pipeline(model_name=SPACY_MODEL):
    if not model_name or model_name == "Rule-based only":
        return None
    if model_name in _SPACY_PIPELINES:
        return _SPACY_PIPELINES[model_name]
    try:
        import spacy
        _SPACY_PIPELINES[model_name] = spacy.load(model_name)
    except (ImportError, OSError):
        _SPACY_PIPELINES[model_name] = None
    return _SPACY_PIPELINES[model_name]


def estimate_experience(text: str) -> Dict[str, Any]:
    """Separate explicitly stated total experience from a dated-work estimate."""
    explicit = re.search(
        r"\b(\d{1,2}(?:\.\d+)?)\+?\s*(?:years?|yrs?)\s+(?:of\s+)?(?:professional\s+)?experience\b",
        text,
        re.IGNORECASE,
    )
    explicit_years = float(explicit.group(1)) if explicit else None
    current_year = datetime.now().year
    intervals = []
    for match in re.finditer(
        r"\b(19\d{2}|20\d{2})\s*(?:-|–|to)\s*(present|current|19\d{2}|20\d{2})\b",
        text,
        re.IGNORECASE,
    ):
        start = int(match.group(1))
        end = current_year if match.group(2).lower() in {"present", "current"} else int(match.group(2))
        if 1980 <= start <= end <= current_year:
            intervals.append((start, end))
    dated_years = sum(max(0, end - start) for start, end in intervals) if intervals else None
    return {
        "explicit_years": explicit_years,
        "estimated_years_from_dates": dated_years,
        "years": explicit_years if explicit_years is not None else dated_years,
        "basis": "explicit" if explicit_years is not None else (
            "dated_work_history" if dated_years is not None else "unknown"
        ),
    }


def extract_entities(
    text: str,
    spacy_model: Optional[str] = None,
    additional_skills: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    """Extract contact and named entities using spaCy when installed."""
    result: Dict[str, Any] = {"organizations": [], "job_titles": [], "degrees": [], "certifications": []}
    model_name = SPACY_MODEL if spacy_model is None else spacy_model
    pipeline = _get_spacy_pipeline(model_name)
    if pipeline is not None:
        doc = pipeline(text[:100000])
        result["organizations"] = sorted({entity.text.strip() for entity in doc.ents if entity.label_ == "ORG"})
    emails = re.findall(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", text, re.IGNORECASE)
    phones = re.findall(r"(?<!\w)(?:\+?\d[\d ().-]{7,}\d)(?!\w)", text)
    degree_terms = ("bachelor", "master", "ph.d", "phd", "b.s.", "b.a.", "b.tech", "m.s.", "m.tech")
    cert_terms = ("certified", "certification", "certificate", "aws certified", "pmp")
    result["emails"] = sorted(set(emails))
    result["phones"] = sorted(set(phone.strip() for phone in phones))
    result["degrees"] = sorted({line.strip() for line in text.splitlines()
                               if any(term in line.lower() for term in degree_terms)})
    result["certifications"] = sorted({line.strip() for line in text.splitlines()
                                      if any(term in line.lower() for term in cert_terms)})
    result["job_titles"] = sorted({line.strip() for line in text.splitlines()
                                  if re.search(r"\b(engineer|developer|analyst|scientist|architect|manager)\b",
                                               line, re.IGNORECASE)})
    result["experience"] = estimate_experience(text)
    result["skills"] = extract_skills(text, additional_skills)
    result["nlp_model"] = model_name if pipeline is not None else "Rule-based fallback"
    return result


def extract_job_requirements(
    text: str,
    additional_skills: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    """Parse required/preferred skill lists and experience from a job description."""
    required_skills, preferred_skills = [], []
    active = None
    for line in text.splitlines():
        lower = line.lower()
        if any(token in lower for token in ("preferred skills", "preferred qualifications", "nice to have")):
            active = "preferred"
        elif any(token in lower for token in ("mandatory skills", "required skills", "required qualifications")):
            active = "required"
        elif active and line.strip().startswith(("-", "*", "•")):
            target = preferred_skills if active == "preferred" else required_skills
            target.extend(extract_skills(line, additional_skills))
    all_skills = extract_skills(text, additional_skills)
    preferred = sorted(set(preferred_skills))
    required = sorted(set(required_skills) - set(preferred))
    if not required and not preferred:
        required = sorted(set(all_skills) - set(preferred))
    exp_match = re.search(r"\b(\d{1,2})\+?\s*(?:years?|yrs?)\b", text, re.IGNORECASE)
    title_match = re.search(r"(?im)^\s*(?:job title:\s*)?([A-Z][^\n]{2,60})\s*$", text)
    return {
        "title": title_match.group(1).strip() if title_match else "Role from job description",
        "required_skills": required,
        "preferred_skills": preferred,
        "required_experience_years": float(exp_match.group(1)) if exp_match else None,
        "education_requirements": [line.strip() for line in text.splitlines()
                                   if re.search(r"\b(degree|bachelor|master|ph\.?d|education)\b",
                                                line, re.IGNORECASE)],
        "certification_requirements": [line.strip() for line in text.splitlines()
                                       if re.search(r"\b(certification|certified|license)\b",
                                                    line, re.IGNORECASE)],
        "all_skills": all_skills,
    }
