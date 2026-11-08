"""Evidence-based recommendation templates that do not invent qualifications."""

from typing import Any, Dict, List


def generate_recommendations(match: Dict[str, Any], resume: Dict[str, Any]) -> List[str]:
    """Generate up to five suggestions grounded in known resume/JD evidence."""
    suggestions: List[str] = []
    missing = match.get("missing_required_skills", [])
    for skill in missing[:2]:
        suggestions.append(
            "If you have hands-on experience with {0}, add a truthful example or project showing how you used it."
            .format(skill)
        )
    for skill in match.get("under_emphasized_skills", [])[:2]:
        suggestions.append(
            "Expand the {0} reference with the project context, your contribution, and a measurable outcome if available."
            .format(skill)
        )
    skills_section = resume.get("sections", {}).get("technical_skills", "")
    if match.get("matched_required_skills") and not skills_section:
        suggestions.append("Add a clearly labeled technical-skills section for the relevant skills already present.")
    if match.get("matched_required_skills") and len(suggestions) < 3:
        suggestions.append(
            "Move the strongest verified requirement matches closer to the top of the resume and connect them to work or project evidence."
        )
    if not suggestions:
        suggestions.extend([
            "Keep the resume focused on accomplishments that are directly relevant to this role.",
            "Where accurate, quantify project scope, outcomes, or operational impact.",
            "Review the job requirements and make sure each relevant qualification is easy to find.",
        ])
    elif len(suggestions) < 3:
        suggestions.extend([
            "Where accurate, quantify the scope or outcome of the projects already listed.",
            "Make sure the experience section clearly identifies your contribution to each relevant project.",
        ])
    return suggestions[:5]
