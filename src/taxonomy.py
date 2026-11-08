"""Extensible canonical skill vocabulary and conservative alias matching."""

import re
from typing import Dict, Iterable, List, Optional, Set, Tuple

SKILLS: Dict[str, Dict[str, object]] = {
    "Python": {"category": "Programming languages", "aliases": ["py"]},
    "Java": {"category": "Programming languages", "aliases": []},
    "JavaScript": {"category": "Programming languages", "aliases": ["js", "ecmascript"]},
    "TypeScript": {"category": "Programming languages", "aliases": ["ts"]},
    "C++": {"category": "Programming languages", "aliases": ["cpp"]},
    "C#": {"category": "Programming languages", "aliases": ["c sharp"]},
    "SQL": {"category": "Programming languages", "aliases": []},
    "HTML": {"category": "Frontend", "aliases": ["html5"]},
    "CSS": {"category": "Frontend", "aliases": ["css3"]},
    "React": {"category": "Frontend", "aliases": ["reactjs", "react.js"]},
    "Angular": {"category": "Frontend", "aliases": ["angularjs"]},
    "Vue": {"category": "Frontend", "aliases": ["vue.js", "vuejs"]},
    "Node.js": {"category": "Backend", "aliases": ["node", "nodejs"]},
    "Django": {"category": "Backend", "aliases": []},
    "Flask": {"category": "Backend", "aliases": []},
    "FastAPI": {"category": "Backend", "aliases": []},
    "Spring Framework": {"category": "Backend", "aliases": ["spring framework", "spring boot"]},
    "REST APIs": {"category": "Backend", "aliases": ["rest api", "restful api", "restful apis"]},
    "PostgreSQL": {"category": "Databases", "aliases": ["postgres", "postgresql"]},
    "MySQL": {"category": "Databases", "aliases": []},
    "MongoDB": {"category": "Databases", "aliases": ["mongo"]},
    "Redis": {"category": "Databases", "aliases": []},
    "AWS": {"category": "Cloud and DevOps", "aliases": ["amazon web services"]},
    "Azure": {"category": "Cloud and DevOps", "aliases": ["microsoft azure"]},
    "Docker": {"category": "Cloud and DevOps", "aliases": []},
    "Kubernetes": {"category": "Cloud and DevOps", "aliases": ["k8s"]},
    "Terraform": {"category": "Cloud and DevOps", "aliases": []},
    "CI/CD": {"category": "Cloud and DevOps", "aliases": ["continuous integration", "continuous delivery"]},
    "Git": {"category": "Tools and platforms", "aliases": ["git version control"]},
    "Linux": {"category": "Tools and platforms", "aliases": []},
    "Pandas": {"category": "Data Science", "aliases": []},
    "NumPy": {"category": "Data Science", "aliases": ["numpy"]},
    "scikit-learn": {"category": "Machine Learning", "aliases": ["sklearn", "scikit learn"]},
    "TensorFlow": {"category": "Machine Learning", "aliases": ["tensorflow"]},
    "PyTorch": {"category": "Machine Learning", "aliases": ["pytorch"]},
    "Machine Learning": {"category": "Machine Learning", "aliases": ["ml"]},
    "Artificial Intelligence": {"category": "AI and NLP", "aliases": ["ai"]},
    "Natural Language Processing": {"category": "AI and NLP", "aliases": ["nlp"]},
    "spaCy": {"category": "AI and NLP", "aliases": ["spacy"]},
    "Transformers": {"category": "AI and NLP", "aliases": ["hugging face transformers"]},
    "Sentence Transformers": {"category": "AI and NLP", "aliases": ["sbert"]},
    "pytest": {"category": "Testing", "aliases": []},
    "Selenium": {"category": "Testing", "aliases": []},
    "Jest": {"category": "Testing", "aliases": []},
    "Power BI": {"category": "Data Science", "aliases": ["powerbi"]},
    "Tableau": {"category": "Data Science", "aliases": []},
    "Apache Spark": {"category": "Data Science", "aliases": ["spark"]},
    "Airflow": {"category": "Data Science", "aliases": ["apache airflow"]},
}

_ALIASES: Dict[str, str] = {}
for _canonical, _details in SKILLS.items():
    for _alias in [_canonical] + list(_details["aliases"]):
        _ALIASES[_alias.lower()] = _canonical


def normalize_skill(value: str) -> str:
    """Return a canonical skill name, preserving unknown values as trimmed text."""
    key = re.sub(r"\s+", " ", value.strip().lower())
    return _ALIASES.get(key, value.strip())


def _pattern(value: str) -> re.Pattern:
    escaped = re.escape(value.lower())
    return re.compile(r"(?<![a-z0-9])" + escaped + r"(?![a-z0-9])", re.IGNORECASE)


_SKILL_PATTERNS: List[Tuple[str, re.Pattern]] = sorted(
    [
        (canonical, _pattern(alias))
        for alias, canonical in _ALIASES.items()
        if len(alias) > 1 or alias in {"ai", "ml", "js", "ts"}
    ],
    key=lambda item: len(item[1].pattern),
    reverse=True,
)


def extract_skills(text: str, additional_skills: Optional[Iterable[str]] = None) -> List[str]:
    """Find known skills with token boundaries and contextual Spring disambiguation."""
    found: Set[str] = set()
    lowered = text.lower()
    for canonical, pattern in _SKILL_PATTERNS:
        if pattern.search(lowered):
            if canonical == "Spring Framework":
                if not re.search(r"\b(spring boot|spring framework|java spring)\b", lowered):
                    continue
            found.add(canonical)
    for skill in additional_skills or ():
        skill = skill.strip()
        if skill and _pattern(skill).search(lowered):
            found.add(skill)
    return sorted(found)


def skill_categories(skills: Iterable[str]) -> Dict[str, List[str]]:
    """Group canonical skills by taxonomy category."""
    categories: Dict[str, List[str]] = {}
    for skill in skills:
        canonical = normalize_skill(skill)
        category = str(SKILLS.get(canonical, {}).get("category", "Other"))
        categories.setdefault(category, []).append(canonical)
    return categories
