"""Explainable weighted scoring with normalized configurable weights."""

import re
from typing import Any, Dict, Optional

from config import DEFAULT_SCORING_WEIGHTS
from src.taxonomy import normalize_skill


def normalize_weights(weights: Dict[str, float]) -> Dict[str, float]:
    """Normalize the four configured scoring weights to exactly 100 percent."""
    keys = list(DEFAULT_SCORING_WEIGHTS)
    values = {key: max(0.0, float(weights.get(key, DEFAULT_SCORING_WEIGHTS[key]))) for key in keys}
    total = sum(values.values())
    if total == 0:
        raise ValueError("At least one scoring weight must be greater than zero.")
    normalized = {key: values[key] * 100.0 / total for key in keys}
    last = keys[-1]
    normalized[last] = 100.0 - sum(normalized[key] for key in keys[:-1])
    return normalized


def calculate_scores(
    match: Dict[str, Any],
    resume_entities: Dict[str, Any],
    job: Dict[str, Any],
    resume_text: str,
    weights: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """Calculate component scores and reweight only components with known evidence."""
    configured = normalize_weights(weights or DEFAULT_SCORING_WEIGHTS)
    required = [normalize_skill(skill) for skill in job.get("required_skills", [])]
    preferred = [normalize_skill(skill) for skill in job.get("preferred_skills", [])]
    matched = set(match["resume_skills"])
    skill_total = sum(2.0 if skill in required else 1.0 for skill in required + preferred)
    skill_earned = sum(2.0 for skill in required if skill in matched) + sum(
        1.0 for skill in preferred if skill in matched
    )
    skills_score = 100.0 * skill_earned / skill_total if skill_total else None

    experience = resume_entities.get("experience", {})
    candidate_years = experience.get("years")
    required_years = job.get("required_experience_years")
    experience_score = None
    if candidate_years is not None and required_years is not None:
        experience_score = 100.0 if required_years <= 0 else min(100.0, 100.0 * candidate_years / required_years)

    degree_text = " ".join(resume_entities.get("degrees", [])).lower()
    cert_text = " ".join(resume_entities.get("certifications", [])).lower()
    education_lines = " ".join(job.get("education_requirements", [])).lower()
    cert_lines = " ".join(job.get("certification_requirements", [])).lower()
    education_present = bool(re.search(r"(?im)^\s*(education|academic background)\s*$", resume_text))
    certification_present = bool(re.search(r"(?im)^\s*(certifications|certificates|licenses)\s*$", resume_text))
    checks = []
    if education_lines and education_present:
        checks.append(100.0 if degree_text else 0.0)
    if cert_lines and certification_present:
        checks.append(100.0 if cert_text else 0.0)
    edu_score = sum(checks) / len(checks) if checks else None

    keywords = set(job.get("all_skills", []))
    keywords.update(required)
    keywords.update(preferred)
    keyword_score = None
    if keywords:
        keyword_score = 100.0 * len(keywords & matched) / len(keywords)

    components = {
        "skills": skills_score,
        "experience": experience_score,
        "education_certifications": edu_score,
        "keyword_coverage": keyword_score,
    }
    available_weight = sum(configured[key] for key, value in components.items() if value is not None)
    if available_weight == 0:
        raise ValueError("Not enough job and candidate information to calculate a match score.")
    final = sum(
        configured[key] * value for key, value in components.items() if value is not None
    ) / available_weight
    return {
        "final_score": round(max(0.0, min(100.0, final)), 2),
        "components": {key: None if value is None else round(value, 2)
                       for key, value in components.items()},
        "weights": configured,
        "unknown_components": [key for key, value in components.items() if value is None],
    }
