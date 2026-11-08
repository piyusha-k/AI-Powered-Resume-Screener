"""Generate original synthetic job descriptions, resumes, and demonstration labels."""

import csv
import json
import random
from pathlib import Path
from typing import Dict, List

from config import EVALUATION_DIR, JOB_DESCRIPTIONS_DIR, SAMPLE_RESUMES_DIR
from src.matcher import analyze_match
from src.nlp_engine import extract_entities, extract_job_requirements
from src.scorer import calculate_scores

JOBS = [
    ("python_developer", "Python Developer", ["Python", "Django", "REST APIs", "PostgreSQL", "Git"],
     ["Docker", "pytest", "AWS"], 2, "Bachelor's degree in Computer Science or equivalent experience.",
     "AWS Certified Developer is a plus."),
    ("full_stack_developer", "Full Stack Developer", ["JavaScript", "TypeScript", "React", "Node.js", "SQL"],
     ["Docker", "AWS", "Jest"], 3, "Bachelor's degree or equivalent professional experience.",
     "A relevant cloud certification is preferred."),
    ("data_scientist", "Data Scientist", ["Python", "SQL", "Pandas", "scikit-learn", "Machine Learning"],
     ["Tableau", "Apache Spark", "AWS"], 3, "Master's degree in Statistics, Data Science, or a related field preferred.",
     "A recognized data science certification is helpful."),
    ("machine_learning_engineer", "Machine Learning Engineer",
     ["Python", "Machine Learning", "PyTorch", "Docker", "AWS"], ["TensorFlow", "Kubernetes", "MLflow"], 4,
     "Bachelor's degree in Computer Science or a related discipline.", "Cloud or machine learning certification preferred."),
    ("nlp_engineer", "NLP Engineer",
     ["Python", "Natural Language Processing", "spaCy", "Transformers", "Machine Learning"],
     ["Sentence Transformers", "PyTorch", "FastAPI"], 3, "Bachelor's degree in Computer Science or Computational Linguistics.",
     "Relevant NLP certification is a plus."),
    ("frontend_developer", "Frontend Developer", ["JavaScript", "TypeScript", "React", "HTML", "CSS"],
     ["Angular", "Vue", "Jest"], 2, "Degree in Computer Science or equivalent portfolio experience.",
     "Accessibility training is preferred."),
    ("backend_developer", "Backend Developer", ["Java", "Spring Framework", "REST APIs", "PostgreSQL", "Docker"],
     ["Redis", "Kubernetes", "AWS"], 3, "Bachelor's degree or comparable experience.", "Cloud certification is a plus."),
    ("devops_engineer", "DevOps Engineer", ["Linux", "Docker", "Kubernetes", "Terraform", "CI/CD"],
     ["AWS", "Azure", "Python"], 3, "Bachelor's degree or equivalent practical experience.",
     "An AWS, Azure, or Kubernetes certification is preferred."),
    ("data_analyst", "Data Analyst", ["SQL", "Python", "Pandas", "Power BI", "Tableau"],
     ["Excel", "Apache Spark", "AWS"], 2, "Bachelor's degree in Analytics, Business, or a related field.",
     "Power BI or Tableau certification is helpful."),
    ("ai_engineer", "AI Engineer", ["Python", "Artificial Intelligence", "Machine Learning", "PyTorch", "FastAPI"],
     ["Natural Language Processing", "TensorFlow", "Docker"], 3,
     "Bachelor's degree in Computer Science, AI, or a related field.", "AI or cloud certifications are preferred."),
]

NAMES = [
    "Avery Morgan", "Jordan Lee", "Casey Patel", "Riley Chen", "Quinn Rivera",
    "Taylor Brooks", "Morgan Kim", "Cameron Diaz", "Reese Turner", "Drew Parker",
    "Skyler Reed", "Rowan Ellis", "Finley Shah", "Emerson Cole", "Dakota James",
    "Harper Singh", "Peyton Cruz", "Sage Bennett", "Alex Monroe", "Kendall Ross",
    "Charlie Nguyen", "Jamie Blake", "Robin Hayes", "Micah Foster", "Sam Taylor",
]

PROFILES = [
    ["Python", "Django", "REST APIs", "PostgreSQL", "Git", "Docker"],
    ["JavaScript", "TypeScript", "React", "Node.js", "SQL", "Jest"],
    ["Python", "SQL", "Pandas", "scikit-learn", "Machine Learning", "Tableau"],
    ["Python", "Machine Learning", "PyTorch", "Docker", "AWS", "Kubernetes"],
    ["Python", "Natural Language Processing", "spaCy", "Transformers", "Machine Learning"],
    ["JavaScript", "TypeScript", "React", "HTML", "CSS", "Jest"],
    ["Java", "Spring Framework", "REST APIs", "PostgreSQL", "Docker", "Redis"],
    ["Linux", "Docker", "Kubernetes", "Terraform", "CI/CD", "AWS"],
    ["SQL", "Python", "Pandas", "Power BI", "Tableau"],
    ["Python", "Artificial Intelligence", "Machine Learning", "PyTorch", "FastAPI"],
    ["Python", "Flask", "REST APIs", "MySQL", "Git"],
    ["HTML", "CSS", "JavaScript", "Vue", "Git"],
    ["Python", "NumPy", "Pandas", "Apache Spark", "SQL"],
    ["Java", "Spring Framework", "MySQL", "Docker", "Git"],
    ["Linux", "Docker", "CI/CD", "Python", "Azure"],
    ["SQL", "Power BI", "Tableau", "Python"],
    ["Python", "Django", "PostgreSQL", "pytest", "AWS"],
    ["TypeScript", "React", "Node.js", "MongoDB", "Docker"],
    ["Python", "Machine Learning", "TensorFlow", "scikit-learn", "NumPy"],
    ["JavaScript", "React", "HTML", "CSS", "Selenium"],
    ["Python", "FastAPI", "PostgreSQL", "Redis", "Docker", "AWS"],
    ["Linux", "Kubernetes", "Terraform", "CI/CD", "Azure"],
    ["Python", "Natural Language Processing", "spaCy", "Sentence Transformers", "PyTorch"],
    ["SQL", "Pandas", "Tableau", "Apache Spark", "Airflow"],
    ["Java", "Spring Framework", "REST APIs", "PostgreSQL", "AWS"],
]

YEARS = [1, 3, 5, 4, 2, 1, 6, 4, 3, 5, 2, 0, 3, 7, 4, 2, 3, 5, 2, 4, 6, 3, 1, 4, 8]

ROLE_RESPONSIBILITIES = {
    "python_developer": [
        "Build maintainable Python services and automation for internal product workflows.",
        "Design API integrations, review changes, and improve test coverage.",
        "Investigate defects and document reliable deployment practices.",
    ],
    "full_stack_developer": [
        "Deliver user-facing product features across browser interfaces and server APIs.",
        "Work with designers to make responsive, accessible experiences.",
        "Maintain data flows and integration tests across the application stack.",
    ],
    "data_scientist": [
        "Analyze structured datasets and communicate assumptions in clear reports.",
        "Build reproducible experiments and validate statistical model performance.",
        "Partner with domain teams to turn findings into measurable product questions.",
    ],
    "machine_learning_engineer": [
        "Operationalize model training and inference workflows for production use.",
        "Monitor model quality, latency, and data changes with the engineering team.",
        "Build reproducible pipelines and document model deployment decisions.",
    ],
    "nlp_engineer": [
        "Develop language-processing pipelines for classification and information extraction.",
        "Evaluate text models against representative examples and document limitations.",
        "Collaborate on scalable services for search, tagging, and document workflows.",
    ],
    "frontend_developer": [
        "Implement responsive, accessible interfaces from product requirements.",
        "Build reusable components and maintain browser-based test coverage.",
        "Profile page performance and collaborate on consistent interaction patterns.",
    ],
    "backend_developer": [
        "Design versioned backend APIs and reliable data-access patterns.",
        "Improve service observability, database performance, and test coverage.",
        "Coordinate secure integrations with frontend and platform teams.",
    ],
    "devops_engineer": [
        "Automate repeatable build, deployment, and infrastructure workflows.",
        "Improve service reliability through monitoring and incident follow-up.",
        "Maintain secure configuration and container orchestration practices.",
    ],
    "data_analyst": [
        "Prepare trustworthy datasets and define clear metric calculations.",
        "Build dashboards that communicate trends to business partners.",
        "Investigate data quality issues and record reproducible analysis steps.",
    ],
    "ai_engineer": [
        "Integrate machine-learning capabilities into reliable application services.",
        "Evaluate model behavior and document quality, safety, and latency trade-offs.",
        "Partner with product teams to validate AI-assisted workflows.",
    ],
}


def _job_text(job) -> str:
    job_id, title, required, preferred, years, education, certification = job
    responsibilities = ROLE_RESPONSIBILITIES[job_id]
    return "\n".join([
        "Job Title: " + title,
        "",
        "Overview",
        "Join a collaborative team delivering maintainable, measurable technology outcomes.",
        "",
        "Responsibilities",
    ] + ["- " + item for item in responsibilities] + [
        "", "Mandatory Skills",
    ] + ["- " + item for item in required] + [
        "", "Preferred Skills",
    ] + ["- " + item for item in preferred] + [
        "", "Experience Requirements", "- At least {0} years of relevant experience.".format(years),
        "", "Education Requirements", "- " + education,
        "", "Certifications", "- " + certification,
    ])


def _resume_text(index: int, skills: List[str]) -> str:
    name = NAMES[index]
    years = YEARS[index]
    start = 2026 - years
    end = "Present" if years else "2025"
    skills_line = ", ".join(skills)
    summary = (
        "Early-career technology professional interested in building reliable, useful software."
        if years <= 1 else
        "Technology professional with {0} years of experience delivering team projects and production improvements."
        .format(years)
    )
    project = (
        "Built a portfolio project using {0}. Documented the design, tested key workflows, "
        "and presented results to project reviewers.".format(", ".join(skills[:3]))
        if skills else "Completed a collaborative technology project and documented the implementation."
    )
    lines = [name, "Candidate profile"]
    if index % 7 != 4:
        lines.extend([
            "Email: candidate{0}@example.com".format(index + 1),
            "Phone: +1 (202) 555-{0:04d}".format(1000 + index),
        ])
    if index % 8 != 3:
        lines.extend(["", "Summary", summary])
    if index % 6 != 2:
        lines.extend(["", "Technical Skills", skills_line])
    if years > 0 and index % 7 != 5:
        lines.extend([
            "", "Work Experience", "Software Engineer | Example Fictional Studio",
            "{0} - {1}".format(start, end),
            "Contributed to team delivery, code review, and quality improvements using {0}."
            .format(", ".join(skills[:2]) if skills else "standard development practices"),
        ])
    if index % 6 != 2:
        lines.extend([
            "", "Education",
            "Bachelor of Science in Computer Science | Example Institute | {0}".format(2025 - index % 5),
        ])
    lines.extend(["", "Projects", project])
    if index % 3 == 0:
        lines.extend([
            "Prepared a short implementation note and checked the result against a repeatable test case.",
        ])
    if index % 2 == 0:
        lines.append("In a fictional portfolio benchmark, improved processing time by 18% across 120 sample records.")
    if index % 4 == 0:
        lines.extend(["", "Certifications", "Example Cloud Fundamentals Certificate"])
    if index % 5 == 1:
        lines.extend([
            "", "Achievements",
            "Presented a fictional portfolio demonstration to a review panel; received positive feedback.",
        ])
    if index % 11 == 10:
        lines.extend(["", "Interests", "Spring is a favorite season for weekend hiking."])
    if index % 3 == 1:
        headings = {
            "summary", "technical skills", "work experience", "education",
            "projects", "certifications", "achievements",
        }
        lines = [line.upper() if line.lower() in headings else line for line in lines]
    return "\n".join(lines)


def _write_docx(path: Path, text: str) -> None:
    from docx import Document
    document = Document()
    for line in text.splitlines():
        if not line.strip():
            continue
        if line.lower() in {
            "summary", "technical skills", "work experience", "education",
            "projects", "certifications", "achievements",
        }:
            document.add_heading(line, level=2)
        else:
            document.add_paragraph(line)
    document.save(str(path))


def _write_pdf(path: Path, text: str) -> None:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    pdf = canvas.Canvas(str(path), pagesize=letter)
    width, height = letter
    y = height - 52
    for line in text.splitlines():
        if y < 48:
            pdf.showPage()
            y = height - 52
        if line.strip():
            pdf.setFont("Helvetica-Bold" if line.lower() in {
                "summary", "technical skills", "work experience", "education",
                "projects", "certifications", "achievements",
            } else "Helvetica", 10)
            pdf.drawString(48, y, line[:105])
        y -= 15
    pdf.save()


def generate() -> None:
    """Create 10 original JDs, 25 mixed-format fictional resumes, and 30 labeled pairs."""
    JOB_DESCRIPTIONS_DIR.mkdir(parents=True, exist_ok=True)
    SAMPLE_RESUMES_DIR.mkdir(parents=True, exist_ok=True)
    EVALUATION_DIR.mkdir(parents=True, exist_ok=True)
    for job in JOBS:
        (JOB_DESCRIPTIONS_DIR / (job[0] + ".txt")).write_text(_job_text(job), encoding="utf-8")
    profiles = []
    for index, skills in enumerate(PROFILES):
        text = _resume_text(index, skills)
        extension = ".pdf" if index % 2 == 0 else ".docx"
        path = SAMPLE_RESUMES_DIR / ("candidate_{0:02d}{1}".format(index + 1, extension))
        if extension == ".pdf":
            _write_pdf(path, text)
        else:
            _write_docx(path, text)
        profiles.append({
            "candidate_id": "candidate_{0:02d}".format(index + 1),
            "filename": path.name,
            "text": text,
            "skills": skills,
        })

    evaluation_rows = []
    random.seed(23)
    for job_index, job in enumerate(JOBS):
        job_text = _job_text(job)
        parsed_job = extract_job_requirements(job_text)
        for offset in range(3):
            candidate_index = (job_index * 3 + offset * 7) % len(profiles)
            profile = profiles[candidate_index]
            resume = {"text": profile["text"]}
            match = analyze_match(resume, parsed_job)
            entities = extract_entities(profile["text"])
            score = calculate_scores(match, entities, parsed_job, profile["text"])["final_score"]
            overlap = len(set(job[2]) & set(profile["skills"])) / max(len(job[2]), 1)
            rating = max(1, min(5, int(round(1 + 4 * overlap + random.uniform(-0.25, 0.25)))))
            evaluation_rows.append({
                "candidate_id": profile["candidate_id"],
                "job_description_id": job[0],
                "human_fit_rating": rating,
                "screening_score": score,
                "label_source": "simulated demonstration label; not a human evaluation",
            })
    with (EVALUATION_DIR / "evaluation_pairs.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=evaluation_rows[0].keys())
        writer.writeheader()
        writer.writerows(evaluation_rows)
    with (SAMPLE_RESUMES_DIR / "sample_manifest.json").open("w", encoding="utf-8") as stream:
        json.dump(
            [{"candidate_id": row["candidate_id"], "filename": row["filename"]} for row in profiles],
            stream, indent=2,
        )
    print("Generated {0} job descriptions, {1} resumes, and {2} evaluation pairs.".format(
        len(JOBS), len(profiles), len(evaluation_rows)
    ))


if __name__ == "__main__":
    generate()
