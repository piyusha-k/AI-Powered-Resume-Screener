"""Candidate/JD similarity, qualification-gap analysis, and evidence snippets."""

import re
from typing import Any, Dict, List, Optional, Sequence

from config import SEMANTIC_MODEL
from src.taxonomy import extract_skills, normalize_skill

_TFIDF_VECTORIZER = None
_SEMANTIC_MODELS = {}
_SEMANTIC_WARNINGS = {}


def _cosine(left, right) -> float:
    import numpy as np
    denominator = float(np.linalg.norm(left) * np.linalg.norm(right))
    return 0.0 if denominator == 0 else float(np.dot(left, right) / denominator)


def similarity_scores(
    job_text: str,
    resume_text: str,
    *,
    enable_semantic: bool = True,
    semantic_model: str = SEMANTIC_MODEL,
) -> Dict[str, Any]:
    """Return TF-IDF and semantic similarity independently; unavailable SBERT is explicit."""
    tfidf_score = 0.0
    global _TFIDF_VECTORIZER
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        _TFIDF_VECTORIZER = _TFIDF_VECTORIZER or TfidfVectorizer(stop_words="english", max_features=20000)
        matrix = _TFIDF_VECTORIZER.fit_transform([job_text, resume_text])
        tfidf_score = float(cosine_similarity(matrix[0:1], matrix[1:2])[0][0])
    except ImportError:
        raise RuntimeError("TF-IDF similarity requires scikit-learn; install requirements.txt.")
    except ValueError as exc:
        raise ValueError("TF-IDF could not find usable terms in the supplied documents.") from exc
    semantic_score = None
    if enable_semantic and semantic_model not in _SEMANTIC_MODELS:
        try:
            from sentence_transformers import SentenceTransformer
            _SEMANTIC_MODELS[semantic_model] = SentenceTransformer(semantic_model)
        except Exception as exc:
            _SEMANTIC_MODELS[semantic_model] = None
            _SEMANTIC_WARNINGS[semantic_model] = str(exc)[:240]
    if enable_semantic and _SEMANTIC_MODELS.get(semantic_model) is not None:
        try:
            embeddings = _SEMANTIC_MODELS[semantic_model].encode(
                [job_text, resume_text], normalize_embeddings=True
            )
            semantic_score = _cosine(embeddings[0], embeddings[1])
        except (OSError, RuntimeError, ValueError):
            semantic_score = None
            _SEMANTIC_WARNINGS[semantic_model] = "Semantic model inference failed."
    return {
        "tfidf": max(0.0, min(1.0, tfidf_score)),
        "semantic": semantic_score,
        "semantic_warning": _SEMANTIC_WARNINGS.get(semantic_model) if enable_semantic else None,
    }


def find_skill_evidence(skill: str, text: str) -> List[str]:
    """Return short original-text snippets containing a known skill alias."""
    aliases = [skill]
    normalized = normalize_skill(skill)
    from src.taxonomy import SKILLS
    aliases.extend(SKILLS.get(normalized, {}).get("aliases", []))
    snippets = []
    for line in text.splitlines():
        if any(re.search(r"(?<!\w)" + re.escape(alias) + r"(?!\w)", line, re.IGNORECASE)
               for alias in aliases):
            snippets.append(line.strip()[:240])
    return snippets[:3]


def analyze_match(
    resume: Dict[str, Any],
    job: Dict[str, Any],
    additional_skills: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    """Identify matched, missing, under-emphasized, and additional skills."""
    text = resume["text"]
    resume_skills = set(extract_skills(text, additional_skills))
    required = set(job.get("required_skills", []))
    preferred = set(job.get("preferred_skills", []))
    requested = required | preferred
    matched_required = sorted(required & resume_skills)
    matched_preferred = sorted(preferred & resume_skills)
    missing_required = sorted(required - resume_skills)
    missing_preferred = sorted(preferred - resume_skills)
    evidence = {skill: find_skill_evidence(skill, text) for skill in sorted(requested & resume_skills)}
    under_emphasized = sorted(
        skill for skill, snippets in evidence.items()
        if snippets and all(len(snippet.split()) < 5 for snippet in snippets)
    )
    return {
        "resume_skills": sorted(resume_skills),
        "matched_required_skills": matched_required,
        "matched_preferred_skills": matched_preferred,
        "missing_required_skills": missing_required,
        "missing_preferred_skills": missing_preferred,
        "additional_relevant_skills": sorted(resume_skills - requested),
        "under_emphasized_skills": under_emphasized,
        "skill_evidence": evidence,
    }
