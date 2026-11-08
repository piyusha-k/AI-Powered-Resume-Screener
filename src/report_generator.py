"""Professional, locally generated candidate screening reports."""

from io import BytesIO
from typing import Any, Dict, List


def generate_pdf_report(result: Dict[str, Any]) -> bytes:
    """Create a readable PDF report for a candidate."""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    except ImportError as exc:
        raise RuntimeError("PDF report generation requires reportlab; install requirements.txt.") from exc

    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer, pagesize=letter, rightMargin=0.65 * inch, leftMargin=0.65 * inch,
        topMargin=0.6 * inch, bottomMargin=0.6 * inch,
    )
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="SmallBody", parent=styles["BodyText"], fontSize=9, leading=12))
    story = [
        Paragraph("Candidate Screening Report", styles["Title"]),
        Paragraph("Candidate: {0}".format(result.get("candidate_name", "Candidate")), styles["Heading2"]),
        Paragraph("Job: {0}".format(result.get("job_title", "Role")), styles["BodyText"]),
        Paragraph("Overall match: {0:.1f}%".format(result["scores"]["final_score"]), styles["Heading2"]),
        Spacer(1, 10),
        Paragraph("Score breakdown", styles["Heading3"]),
    ]
    score_rows = [["Component", "Score", "Configured weight"]]
    labels = {
        "skills": "Weighted skills",
        "experience": "Experience",
        "education_certifications": "Education / certifications",
        "keyword_coverage": "Keyword coverage",
    }
    for key, label in labels.items():
        value = result["scores"]["components"][key]
        score_rows.append([
            label, "Unknown" if value is None else "{0:.1f}%".format(value),
            "{0:.1f}%".format(result["scores"]["weights"][key]),
        ])
    table = Table(score_rows, colWidths=[3.5 * inch, 1.3 * inch, 1.4 * inch])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#15345b")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#d5deea")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f3f6fa")]),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.extend([table, Spacer(1, 10)])

    sections = [
        ("Matched skills", result["match"]["matched_required_skills"] +
         result["match"]["matched_preferred_skills"]),
        ("Missing mandatory skills", result["match"]["missing_required_skills"]),
        ("Missing preferred skills", result["match"]["missing_preferred_skills"]),
        ("Additional relevant skills", result["match"]["additional_relevant_skills"]),
        ("Education", result["entities"].get("degrees", [])),
        ("Certifications", result["entities"].get("certifications", [])),
        ("Relevant experience", [
            "{0} years ({1})".format(
                result["entities"]["experience"]["years"],
                result["entities"]["experience"]["basis"],
            )
        ] if result["entities"]["experience"]["years"] is not None else []),
        ("Recommendations", result["recommendations"]),
    ]
    for heading, items in sections:
        story.append(Paragraph(heading, styles["Heading3"]))
        story.append(Paragraph(
            "<br/>".join(_escape(item) for item in items) if items else "No information identified.",
            styles["SmallBody"],
        ))
    similarities = result.get("similarity", {})
    story.extend([
        Spacer(1, 8),
        Paragraph("TF-IDF similarity: {0:.1f}%".format(100 * similarities.get("tfidf", 0.0)), styles["SmallBody"]),
        Paragraph(
            "Semantic similarity: {0}".format(
                "Unavailable" if similarities.get("semantic") is None
                else "{0:.1f}%".format(100 * similarities["semantic"])
            ), styles["SmallBody"],
        ),
        Paragraph("Generated: {0}".format(result.get("timestamp", "Not recorded")), styles["SmallBody"]),
        Paragraph("Screening scores support review and are not an automated hiring decision.", styles["SmallBody"]),
    ])
    document.build(story)
    return buffer.getvalue()


def _escape(text: str) -> str:
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
