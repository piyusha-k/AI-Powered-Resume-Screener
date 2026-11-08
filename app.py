"""Streamlit interface for local resume screening."""

import html
import logging
import re
import time
from pathlib import Path

import pandas as pd
import streamlit as st

from config import (
    DEFAULT_SCORING_WEIGHTS,
    JOB_DESCRIPTIONS_DIR,
    MAX_UPLOAD_BYTES,
    SEMANTIC_MODEL,
    SPACY_MODEL,
)
from src.extractor import extract_document
from src.report_generator import generate_pdf_report
from src.scorer import normalize_weights
from src.screening import screen_candidate
from src.taxonomy import SKILLS
from src.utils import append_processing_log, get_upload_bytes, logger

st.set_page_config(
    page_title="Resume Screener",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .stApp {
      background:
        radial-gradient(ellipse at 8% 2%, rgba(201, 230, 255, .55), transparent 34%),
        radial-gradient(ellipse at 94% 8%, rgba(238, 216, 255, .42), transparent 30%),
        #f7f8fc;
      color: #172b4d;
    }
    [data-testid="stSidebar"] {
      background: linear-gradient(165deg, #123657 0%, #173b60 48%, #38346f 100%);
    }
    [data-testid="stSidebar"] * { color: #f5f8fc; }
    [data-testid="stMetric"] {
      background: rgba(255, 255, 255, .92);
      padding: 18px;
      border-radius: 18px;
      border: 1px solid #e4e9f4;
      box-shadow: 0 5px 18px rgba(34, 56, 94, .06);
    }
    .hero {
      padding: 1.45rem 1.7rem;
      background: linear-gradient(112deg, #183d63 0%, #276ea2 58%, #7462ae 100%);
      border: 1px solid rgba(255, 255, 255, .28);
      border-radius: 22px;
      color: white;
      margin-bottom: 1.35rem;
      box-shadow: 0 12px 30px rgba(44, 78, 130, .16);
    }
    .stButton > button,
    .stDownloadButton > button {
      min-height: 2.7rem;
      border-radius: 14px;
      border: 1px solid #d5deef;
      background: linear-gradient(135deg, #fff 0%, #eef5ff 100%);
      color: #25466d;
      font-weight: 600;
      transition: transform .16s ease, box-shadow .16s ease, border-color .16s ease;
      box-shadow: 0 3px 10px rgba(35, 65, 110, .07);
    }
    .stButton > button:hover,
    .stDownloadButton > button:hover {
      transform: translateY(-1px);
      border-color: #9dbbe4;
      box-shadow: 0 7px 17px rgba(35, 65, 110, .13);
      color: #173b63;
    }
    .stButton > button[kind="primary"] {
      border: 0;
      color: white;
      background: linear-gradient(110deg, #1977a8, #5863ba);
      box-shadow: 0 6px 16px rgba(48, 91, 157, .23);
    }
    .stButton > button[kind="primary"]:hover {
      color: white;
      box-shadow: 0 9px 20px rgba(48, 91, 157, .30);
    }
    [data-testid="stTextInput"] input,
    [data-testid="stTextArea"] textarea,
    [data-testid="stSelectbox"] [data-baseweb="select"] > div,
    [data-testid="stFileUploader"] section {
      border-radius: 12px;
    }
    [data-testid="stExpander"] {
      background: rgba(255, 255, 255, .75);
      border: 1px solid #e4e9f4;
      border-radius: 14px;
    }
    .muted { color: #66758a; }
    </style>
    """,
    unsafe_allow_html=True,
)

if "results" not in st.session_state:
    st.session_state.results = []
if "job_descriptions" not in st.session_state:
    st.session_state.job_descriptions = []
if "weights" not in st.session_state:
    st.session_state.weights = dict(DEFAULT_SCORING_WEIGHTS)
if "nlp_model" not in st.session_state:
    st.session_state.nlp_model = SPACY_MODEL
if "semantic_enabled" not in st.session_state:
    st.session_state.semantic_enabled = True
if "semantic_model" not in st.session_state:
    st.session_state.semantic_model = SEMANTIC_MODEL
if "additional_skills" not in st.session_state:
    st.session_state.additional_skills = []

st.sidebar.title("Resume Screener")
page = st.sidebar.radio(
    "Workspace",
    ["Dashboard", "Resume Screening", "Candidate Results", "Evaluation", "Settings"],
)


def _sample_jds():
    return sorted(JOB_DESCRIPTIONS_DIR.glob("*.txt"))


def _highlight_skill(snippet, skill):
    aliases = [skill] + list(SKILLS.get(skill, {}).get("aliases", []))
    pattern = re.compile(
        r"(?<!\w)(?:" + "|".join(re.escape(alias) for alias in sorted(aliases, key=len, reverse=True))
        + r")(?!\w)",
        re.IGNORECASE,
    )
    chunks = []
    start = 0
    for match in pattern.finditer(snippet):
        chunks.extend([
            html.escape(snippet[start:match.start()]),
            "<mark>" + html.escape(match.group(0)) + "</mark>",
        ])
        start = match.end()
    chunks.append(html.escape(snippet[start:]))
    return "".join(chunks)


def _load_job_text():
    sample_files = _sample_jds()
    options = ["Paste or upload a job description"] + [path.stem.replace("_", " ") for path in sample_files]
    choice = st.selectbox("Choose a job description", options)
    if choice != options[0]:
        path = next(item for item in sample_files if item.stem.replace("_", " ") == choice)
        return path.read_text(encoding="utf-8"), None
    job_text = st.text_area("Paste job description", height=220, key="job_text")
    uploaded = st.file_uploader("Or upload a job description", type=["txt", "pdf", "docx"], key="job_file")
    if uploaded is not None:
        name = getattr(uploaded, "name", "job description")
        try:
            name, content = get_upload_bytes(uploaded)
            job_text = extract_document(name, content, document_kind="job")["text"]
            st.caption("Loaded job description from " + name)
        except Exception as exc:
            logger.exception("Could not read uploaded job description %s", Path(name).name)
            st.error("Could not read the job description: " + str(exc))
    return job_text, choice


if page == "Dashboard":
    st.markdown(
        '<div class="hero"><h1>AI-powered resume screening</h1>'
        '<p>Local, explainable candidate comparisons. Screening scores support review; '
        'they are not an automated hiring decision.</p></div>',
        unsafe_allow_html=True,
    )
    results = st.session_state.results
    columns = st.columns(4)
    columns[0].metric("Resumes screened", len(results))
    columns[1].metric("Job descriptions", len(st.session_state.job_descriptions))
    columns[2].metric(
        "Average match",
        "{:.1f}%".format(sum(item["scores"]["final_score"] for item in results) / len(results))
        if results else "—",
    )
    columns[3].metric(
        "Highest match",
        "{:.1f}%".format(max(item["scores"]["final_score"] for item in results)) if results else "—",
    )
    st.subheader("Recent screening activity")
    if results:
        st.dataframe(
            pd.DataFrame([
                {"Candidate": item["candidate_name"], "Role": item["job_title"],
                 "Match": item["scores"]["final_score"], "File": item["filename"]}
                for item in results[-8:]
            ]).sort_values("Match", ascending=False),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No resumes screened in this session. Start in Resume Screening.")
    st.caption("Files are processed locally. Resume text is not written to the processing log.")

elif page == "Resume Screening":
    st.title("Resume Screening")
    job_text, selected_jd = _load_job_text()
    uploads = st.file_uploader(
        "Upload one or more resumes (PDF or DOCX, max 10 MB each)",
        type=["pdf", "docx"],
        accept_multiple_files=True,
        key="resume_files",
    )
    st.caption("Up to 10 MB per file. Scanned PDFs use OCR only when local OCR tools are installed.")
    if st.button("Start screening", type="primary", disabled=not uploads or not job_text.strip()):
        failures = []
        job_id = selected_jd or "custom"
        if job_text not in st.session_state.job_descriptions:
            st.session_state.job_descriptions.append(job_text)
        progress = st.progress(0.0, text="Preparing screening")
        status = st.empty()
        for index, uploaded in enumerate(uploads):
            started = time.perf_counter()
            name = getattr(uploaded, "name", "unknown")
            try:
                name, content = get_upload_bytes(uploaded)
                resume = extract_document(name, content)
                candidate_result = screen_candidate(
                    resume,
                    job_text,
                    st.session_state.weights,
                    spacy_model=st.session_state.nlp_model,
                    enable_semantic=st.session_state.semantic_enabled,
                    semantic_model=st.session_state.semantic_model,
                    additional_skills=st.session_state.additional_skills,
                )
                candidate_result["job_id"] = job_id
                st.session_state.results = [
                    item for item in st.session_state.results
                    if not (item["filename"] == name and item["job_title"] == candidate_result["job_title"])
                ] + [candidate_result]
                append_processing_log(
                    name, time.perf_counter() - started, True,
                    len(candidate_result["match"]["resume_skills"]),
                    candidate_result["scores"]["final_score"],
                )
                status.success("Screened {0}: {1:.1f}% match".format(
                    name, candidate_result["scores"]["final_score"]
                ))
            except Exception as exc:
                logger.exception("Could not screen uploaded file %s", Path(name).name)
                append_processing_log(
                    name, time.perf_counter() - started, False, 0, error=str(exc)
                )
                failures.append("{0}: {1}".format(name, exc))
                status.error("Could not screen {0}: {1}".format(name, exc))
            progress.progress((index + 1) / len(uploads), text="Processed {0} of {1}".format(index + 1, len(uploads)))
        if failures:
            st.warning("{0} file(s) could not be screened. They were not assigned zero scores.".format(len(failures)))
        st.success("Screening complete. Open Candidate Results to review rankings.")

elif page == "Candidate Results":
    st.title("Candidate Results")
    results = st.session_state.results
    if not results:
        st.info("No candidates yet. Process resumes from the Resume Screening page.")
    else:
        minimum = st.slider("Minimum match score", 0, 100, 0)
        rows = []
        for index, item in enumerate(results):
            rows.append({
                "Candidate": item["candidate_name"],
                "Match %": item["scores"]["final_score"],
                "TF-IDF %": round(100 * item["similarity"]["tfidf"], 1),
                "Semantic %": None if item["similarity"]["semantic"] is None
                else round(100 * item["similarity"]["semantic"], 1),
                "Matched skills": ", ".join(item["match"]["matched_required_skills"] +
                                             item["match"]["matched_preferred_skills"]),
                "Missing required": ", ".join(item["match"]["missing_required_skills"]),
                "Experience (years)": item["entities"]["experience"]["years"],
                "Role": item["job_title"],
                "_index": index,
            })
        frame = pd.DataFrame(rows)
        frame["Rank"] = frame["Match %"].rank(method="min", ascending=False).astype(int)
        displayed = frame[frame["Match %"] >= minimum].drop(columns="_index")
        sort_column = st.selectbox("Sort by", ["Match %", "Candidate", "TF-IDF %"])
        displayed = displayed.sort_values(sort_column, ascending=(sort_column == "Candidate"))
        displayed = displayed[["Rank"] + [column for column in displayed.columns if column != "Rank"]]
        st.dataframe(displayed, use_container_width=True, hide_index=True)
        st.download_button(
            "Export results as CSV",
            displayed.to_csv(index=False).encode("utf-8"),
            file_name="candidate_screening_results.csv",
            mime="text/csv",
        )
        selected = st.selectbox(
            "Candidate details",
            range(len(results)),
            format_func=lambda index: "{0} — {1:.1f}%".format(
                results[index]["candidate_name"], results[index]["scores"]["final_score"]
            ),
        )
        item = results[selected]
        details, report = st.columns([3, 1])
        with details:
            st.subheader(item["candidate_name"])
            st.metric("Explainable match score", "{:.1f}%".format(item["scores"]["final_score"]))
            st.write("**Role:** " + item["job_title"])
            st.write("**Score breakdown**")
            score_frame = pd.DataFrame([
                {"Component": key.replace("_", " ").title(),
                 "Score": value, "Configured weight": item["scores"]["weights"][key]}
                for key, value in item["scores"]["components"].items()
            ])
            st.dataframe(score_frame, hide_index=True, use_container_width=True)
            if item["scores"]["unknown_components"]:
                st.caption("Unknown rather than treated as gaps: " +
                           ", ".join(item["scores"]["unknown_components"]))
            st.write("**Skills found:** " + ", ".join(item["match"]["resume_skills"]))
            st.write("**Education:** " + ", ".join(item["entities"]["degrees"]) if item["entities"]["degrees"] else "**Education:** Not identified")
            st.write("**Certifications:** " + ", ".join(item["entities"]["certifications"]) if item["entities"]["certifications"] else "**Certifications:** Not identified")
            st.write("**Contact:** " + ", ".join(item["entities"]["emails"] + item["entities"]["phones"])
                     if item["entities"]["emails"] or item["entities"]["phones"] else "**Contact:** Not identified")
            st.write("**Organizations:** " + ", ".join(item["entities"]["organizations"])
                     if item["entities"]["organizations"] else "**Organizations:** Not identified")
            matched_required = item["match"]["matched_required_skills"]
            missing_required = item["match"]["missing_required_skills"]
            missing_preferred = item["match"]["missing_preferred_skills"]
            if matched_required:
                st.success("Matched mandatory skills: " + ", ".join(matched_required))
            if missing_required:
                st.error("Missing mandatory skills: " + ", ".join(missing_required))
            elif item["job"]["required_skills"]:
                st.success("All identified mandatory skills are present.")
            if missing_preferred:
                st.warning("Missing preferred skills: " + ", ".join(missing_preferred))
            exp = item["entities"]["experience"]
            st.write("**Experience:** {0} years ({1})".format(exp["years"], exp["basis"])
                     if exp["years"] is not None else "**Experience:** Not identified")
            required_years = item["job"]["required_experience_years"]
            if required_years is not None and exp["years"] is not None:
                gap = max(0.0, required_years - exp["years"])
                st.write("**Potential experience gap:** {0} years".format(gap) if gap else
                         "**Potential experience gap:** None identified")
            elif required_years is not None:
                st.write("**Potential experience gap:** Unknown (resume experience not identified)")
            st.write("**Additional relevant skills:** " +
                     (", ".join(item["match"]["additional_relevant_skills"]) or "None identified"))
            st.write("**Under-emphasized skills:** " +
                     (", ".join(item["match"]["under_emphasized_skills"]) or "None identified"))
            st.write("**Recommendations**")
            for recommendation in item["recommendations"]:
                st.markdown("- " + recommendation)
            st.write("**Resume evidence snippets**")
            for skill, snippets in item["match"]["skill_evidence"].items():
                with st.expander(skill):
                    for snippet in snippets:
                        st.markdown(_highlight_skill(snippet, skill), unsafe_allow_html=True)
            with st.expander("Extracted resume text"):
                st.text(item["resume"]["text"][:15000])
        with report:
            st.metric("TF-IDF similarity", "{:.1f}%".format(100 * item["similarity"]["tfidf"]))
            semantic = item["similarity"]["semantic"]
            st.metric("Semantic similarity", "Unavailable" if semantic is None else "{:.1f}%".format(100 * semantic))
            if item["similarity"].get("semantic_warning"):
                st.warning(
                    "Semantic similarity unavailable; TF-IDF remains active. "
                    + item["similarity"]["semantic_warning"]
                )
            st.caption("Document similarity is separate from the final match score.")
            st.download_button(
                "Download PDF report",
                generate_pdf_report(item),
                file_name="screening_{0}.pdf".format(Path(item["filename"]).stem),
                mime="application/pdf",
            )

elif page == "Evaluation":
    st.title("Evaluation")
    st.info("Bundled fit ratings are simulated demonstration labels, not genuine human evaluations.")
    eval_path = Path(__file__).parent / "data" / "evaluation" / "evaluation_pairs.csv"
    if eval_path.exists():
        frame = pd.read_csv(eval_path)
        st.metric("Evaluation pairs", len(frame))
        if {"human_fit_rating", "screening_score"}.issubset(frame.columns):
            from src.evaluator import evaluate_pairs
            evaluation = evaluate_pairs(frame)
            metric, count = st.columns(2)
            metric.metric("Spearman correlation", "Not available" if evaluation["coefficient"] is None
                          else "{:.3f}".format(evaluation["coefficient"]))
            count.metric("Valid rated pairs", evaluation["pair_count"])
            st.caption("P-value: {0}".format(
                "Not available" if evaluation["p_value"] is None else "{:.4g}".format(evaluation["p_value"])
            ))
            if evaluation["pair_count"]:
                st.scatter_chart(evaluation["pairs"], x="human_fit_rating", y="screening_score")
                error_data = evaluation["pairs"].copy()
                error_data["rating_scaled_to_100"] = error_data["human_fit_rating"] * 20
                error_data["absolute_difference"] = (
                    error_data["screening_score"] - error_data["rating_scaled_to_100"]
                ).abs()
                st.caption(
                    "Descriptive error view only: fit ratings are multiplied by 20 for a rough scale comparison; "
                    "this is not a validated error metric."
                )
                st.dataframe(
                    error_data.sort_values("absolute_difference", ascending=False).head(10),
                    use_container_width=True,
                    hide_index=True,
                )
        st.dataframe(frame, use_container_width=True, hide_index=True)
        st.download_button("Download evaluation CSV", frame.to_csv(index=False).encode("utf-8"),
                           "evaluation_pairs.csv", "text/csv")
    else:
        st.warning("Sample evaluation data is not generated. Run python src/generate_sample_data.py.")
    st.subheader("Replace demonstration ratings")
    st.caption("Upload a CSV with candidate_id, job_description_id, human_fit_rating (1–5), and screening_score.")
    ratings = st.file_uploader("Human-rated evaluation CSV", type=["csv"], key="ratings")
    if ratings is not None:
        try:
            from src.evaluator import evaluate_pairs
            rated = pd.read_csv(ratings)
            evaluation = evaluate_pairs(rated)
            st.write("Valid evaluation pairs: {0}".format(evaluation["pair_count"]))
            if evaluation["coefficient"] is not None:
                st.metric("Spearman ρ", "{:.3f}".format(evaluation["coefficient"]))
        except (ValueError, KeyError) as exc:
            st.error(str(exc))

elif page == "Settings":
    st.title("Settings")
    st.subheader("Scoring weights")
    st.caption("Weights are normalized to 100% automatically. Unknown evidence is excluded and remaining components are rescaled.")
    keys = list(DEFAULT_SCORING_WEIGHTS)
    labels = {
        "skills": "Skill overlap",
        "experience": "Experience alignment",
        "education_certifications": "Education and certifications",
        "keyword_coverage": "Keyword coverage",
    }
    current = st.session_state.weights
    columns = st.columns(2)
    updated = {}
    for index, key in enumerate(keys):
        updated[key] = columns[index % 2].slider(
            labels[key], 0, 100, int(current.get(key, DEFAULT_SCORING_WEIGHTS[key])),
            key="weight_" + key,
        )
    if sum(updated.values()) == 0:
        normalized = st.session_state.weights
        st.warning("At least one component must have a non-zero weight; keeping previous effective weights.")
    else:
        normalized = normalize_weights(updated)
        st.session_state.weights = normalized
    st.write("Effective weights: " + " · ".join(
        "{0} {1:.1f}%".format(labels[key], normalized[key]) for key in keys
    ))
    st.subheader("NLP and semantic settings")
    st.session_state.nlp_model = st.selectbox(
        "Entity extraction",
        [SPACY_MODEL, "Rule-based only"],
        index=0 if st.session_state.nlp_model == SPACY_MODEL else 1,
    )
    st.session_state.semantic_enabled = st.checkbox(
        "Enable semantic similarity (optional model download)",
        value=st.session_state.semantic_enabled,
    )
    st.session_state.semantic_model = st.text_input(
        "Sentence Transformers model",
        value=st.session_state.semantic_model,
        help="Default: sentence-transformers/all-MiniLM-L6-v2",
    )
    custom_skill_text = st.text_area(
        "Additional exact-match skill terms (comma-separated)",
        value=", ".join(st.session_state.additional_skills),
        help="Add project-specific skill names not present in the built-in taxonomy. Matching is literal and case-insensitive.",
    )
    st.session_state.additional_skills = sorted({
        skill.strip() for skill in custom_skill_text.split(",") if skill.strip()
    })
    st.write("Upload limit: {0} MB per file.".format(MAX_UPLOAD_BYTES // (1024 * 1024)))
    st.write("Skill taxonomy: editable in `src/taxonomy.py`.")
