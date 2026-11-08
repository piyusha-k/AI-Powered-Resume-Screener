"""End-to-end orchestration for scoring one resume against one job description."""

from datetime import datetime, timezone
from typing import Any, Dict, Optional, Sequence

from config import SEMANTIC_MODEL
from src.matcher import analyze_match, similarity_scores
from src.nlp_engine import extract_entities, extract_job_requirements
from src.recommender import generate_recommendations
from src.scorer import calculate_scores


def screen_candidate(
    resume: Dict[str, Any],
    job_text: str,
    weights: Optional[Dict[str, float]] = None,
    *,
    spacy_model: Optional[str] = None,
    enable_semantic: bool = True,
    semantic_model: str = SEMANTIC_MODEL,
    additional_skills: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    """Analyze and score a successfully extracted resume."""
    if not resume.get("text", "").strip():
        raise ValueError("Resume text is empty; refusing to score an unreadable document.")
    job = extract_job_requirements(job_text, additional_skills)
    entities = extract_entities(resume["text"], spacy_model, additional_skills)
    match = analyze_match(resume, job, additional_skills)
    scores = calculate_scores(match, entities, job, resume["text"], weights)
    similarities = similarity_scores(
        job_text,
        resume["text"],
        enable_semantic=enable_semantic,
        semantic_model=semantic_model,
    )
    lines = [line.strip() for line in resume["text"].splitlines() if line.strip()]
    candidate_name = lines[0][:100] if lines else "Candidate"
    return {
        "candidate_name": candidate_name,
        "filename": resume.get("filename", ""),
        "job_title": job["title"],
        "job": job,
        "entities": entities,
        "match": match,
        "scores": scores,
        "similarity": similarities,
        "recommendations": generate_recommendations(match, resume),
        "resume": resume,
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
