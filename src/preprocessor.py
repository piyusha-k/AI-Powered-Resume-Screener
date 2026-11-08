"""Resume text cleanup and section identification."""

import re
from typing import Dict, List

from src.utils import clean_text

SECTION_ALIASES = {
    "contact": ("contact", "personal details"),
    "summary": ("summary", "profile", "professional summary", "objective"),
    "education": ("education", "academic background", "academics"),
    "technical_skills": ("technical skills", "skills", "technologies", "tech stack"),
    "work_experience": ("experience", "work experience", "employment", "professional experience"),
    "projects": ("projects", "selected projects", "personal projects"),
    "certifications": ("certifications", "certificates", "licenses"),
    "achievements": ("achievements", "awards", "honors"),
}
_HEADINGS = {
    re.sub(r"[^a-z ]", "", alias.lower()): section
    for section, aliases in SECTION_ALIASES.items()
    for alias in aliases
}


def detect_sections(text: str) -> Dict[str, str]:
    """Split text by recognizable resume headings; unknown text remains under other."""
    sections: Dict[str, List[str]] = {"other": []}
    current = "other"
    for line in clean_text(text).splitlines():
        key = re.sub(r"[^a-z ]", "", line.lower()).strip()
        key = re.sub(r"\s+", " ", key)
        detected = _HEADINGS.get(key)
        if detected:
            current = detected
            sections.setdefault(current, [])
        else:
            sections.setdefault(current, []).append(line.strip())
    return {
        name: "\n".join(lines).strip()
        for name, lines in sections.items()
        if "\n".join(lines).strip()
    }

