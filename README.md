# AI-Powered Resume Screener

A local Streamlit application that extracts resume information, compares candidates with job descriptions, and presents transparent screening evidence. Scores are decision-support signals; they must not be used as an automated hiring decision.

## Features

- Batch PDF and DOCX resume uploads and TXT/PDF/DOCX job descriptions.
- PDF text extraction with optional Tesseract OCR fallback for scanned documents.
- Rule-based skill normalization and extraction, optional spaCy organization entities, and experience estimates that distinguish explicit statements from dated work history.
- Separate TF-IDF and optional Sentence Transformers similarity measures.
- Configurable, weighted match score with required/preferred skill distinction and unknown data handled separately from a qualification gap.
- Candidate ranking, skill gaps, evidence snippets, recommendations, CSV export, and downloadable PDF reports.
- Settings for score weights, spaCy/semantic similarity behavior, and additional exact-match taxonomy terms.
- Evaluation view with 30 simulated demonstration rating pairs and Spearman correlation. Ratings are explicitly not genuine human evaluations.
- Synthetic data generator for 10 original job descriptions and 25 fictional PDF/DOCX resumes.
- Local processing and minimal processing logs; extracted resume text is not logged.

## Architecture

| Path | Responsibility |
| --- | --- |
| `app.py` | Streamlit dashboard, screening flow, results, evaluation, and settings |
| `config.py` | Paths, supported formats, model names, and scoring defaults |
| `src/extractor.py` | PDF, DOCX, and text extraction; optional OCR |
| `src/preprocessor.py` | Text cleanup and resume-section recognition |
| `src/nlp_engine.py` | spaCy enhancement and rule-based entity/requirement extraction |
| `src/taxonomy.py` | Skill aliases, categories, normalization, and conservative matching |
| `src/matcher.py` | TF-IDF/SBERT similarity, skill gaps, and evidence snippets |
| `src/scorer.py` | Configurable weighted score and unknown-component handling |
| `src/recommender.py` | Resume recommendations grounded in extracted content |
| `src/report_generator.py` | Candidate PDF reports |
| `src/evaluator.py` | Evaluation-data validation and Spearman statistics |
| `src/screening.py` | End-to-end candidate screening orchestration |
| `src/generate_sample_data.py` | Rebuild sample JDs, resumes, and demonstration labels |
| `tests/` | Unit tests for extraction, taxonomy, matching, and scoring |
| `data/` | Synthetic sample JDs, resumes, and evaluation CSV |
| `reports/` | Reserved for user-generated reports; generated files are ignored by Git |

```text
data/
  job_descriptions/   10 original TXT job descriptions
  sample_resumes/     25 synthetic PDF/DOCX resumes and manifest
  evaluation/         30-pair simulated evaluation CSV and runtime processing log
src/                  Modular extraction, NLP, scoring, reporting, and data generation
tests/                Unit tests
assets/               Optional project assets
reports/              Reserved for generated reports
```

## Technology

Python 3.10+, Streamlit, spaCy, pypdf, python-docx, pytesseract/pdf2image (optional OCR), scikit-learn, sentence-transformers (optional semantic similarity), pandas, NumPy, SciPy, and ReportLab.

The app does not require OpenAI or other paid API credentials. TF-IDF and rule-based extraction are the local baseline. The optional Sentence Transformers model is `sentence-transformers/all-MiniLM-L6-v2`; its first use may download model files. If it is unavailable, the TF-IDF score remains usable and semantic similarity is shown as unavailable. Additional taxonomy terms can be configured from Settings; these are matched literally and case-insensitively.

## Installation

### Windows PowerShell

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### Linux/macOS

```bash
python3.10 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

The spaCy model improves organization entity extraction; a missing model does not prevent the rule-based baseline from running.

### OCR setup (optional)

OCR fallback requires both the Tesseract executable and Poppler:

- **Windows:** install Tesseract (for example, the UB Mannheim Windows build) and Poppler for Windows. Add their `tesseract.exe` and Poppler `bin` directories to `PATH`. If Tesseract is not on `PATH`, configure `pytesseract.pytesseract.tesseract_cmd` for your machine.
- **Ubuntu/Debian:** `sudo apt-get install tesseract-ocr poppler-utils`
- **macOS with Homebrew:** `brew install tesseract poppler`

Text-based PDF extraction works without OCR tools. Scanned PDFs that cannot be read with OCR are reported as processing errors and are not given a zero score.

## User guide

### Start the app

Open PowerShell or a VS Code terminal in the project folder. Use Python 3.10 or later (Python 3.11 is a good choice). If you have not created the environment yet:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

For later sessions, activate the existing environment instead:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell says script execution is disabled, use the environment's Python directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m spacy download en_core_web_sm
```

Start Streamlit from the project root:

```powershell
streamlit run app.py
```

Open the **Local URL** shown in the terminal (usually `http://localhost:8501`). Keep that terminal open while using the app. Press **Ctrl+C** in that terminal to stop it. If port 8501 is already occupied, Streamlit will print another local port to use.

### Dashboard

Choose a page from the left-hand **Workspace** menu:

- **Dashboard** summarizes screening results held in the current Streamlit session: number of screened resumes and job descriptions, average and highest score, and recent activity.
- Results are kept in session state while you navigate between pages. They are not a permanent database; save any reports or CSV files you need before closing or restarting the app.

### Screen resumes

1. Select **Resume Screening** in the sidebar.
2. Choose a job description:
   - Pick one of the bundled sample roles from the dropdown, or
   - Keep **Paste or upload a job description** selected and paste the text, or upload a `.txt`, `.pdf`, or `.docx` job-description file.
3. Use **Upload one or more resumes** to select PDF and/or DOCX files. Multiple files can be screened against the selected job description in one run.
4. Click **Start screening**. Follow the progress bar and per-file status messages.
5. Open **Candidate Results** after processing to inspect scores and candidate details.

Each upload is limited to 10 MB. Resume uploads must be PDF or DOCX; TXT is supported only for job descriptions. Text-based PDFs and DOCX files work without OCR. Scanned PDFs require the optional local Tesseract and Poppler setup described above. If a document cannot be read, it is reported as an error and is not treated as an ordinary zero-score candidate.

If Sentence Transformers is enabled, its model may download the first time it is used. This can take a while and requires access to the model files. If the download or inference fails, the app reports that semantic similarity is unavailable; TF-IDF remains a separate available comparison. You can turn semantic similarity off in **Settings** for a faster, network-independent screening run after dependencies are installed.

### Review candidate results

On **Candidate Results**:

- Use **Minimum match score** to filter the table and **Sort by** to change its ordering. The rank column reflects the candidate's score among all results in this session.
- Choose **Export results as CSV** to save the currently displayed table.
- Select a candidate in **Candidate details** to inspect the score and its component breakdown, extracted skills, matched and missing qualifications, estimated or stated experience, education, certifications, recommendations, and source-text evidence snippets.
- Compare TF-IDF and semantic similarity separately; they are document-similarity measures, not the overall match score.
- Click **Download PDF report** in the detail panel to save a report for that candidate.

When an education, certification, or experience component cannot be determined, it may be shown as unknown and excluded from the score rather than treated as a definite qualification gap. Check the original resume and evidence yourself: extraction and rule-based matching can miss context or misinterpret a document.

### Evaluation

Open **Evaluation** to review the bundled 30 candidate/job pairs, their simulated 1–5 labels, screening scores, Spearman correlation, p-value, comparison chart, and largest differences. These labels are generated for demonstration; they are **not human evaluations** and do not establish model accuracy, fairness, or suitability for hiring.

To try independently collected ratings, upload a CSV on the Evaluation page. It must include numeric `human_fit_rating` values from 1 to 5 and numeric `screening_score` values. Include `candidate_id` and `job_description_id` too, so each rating can be traced to the pair reviewed. The app computes the correlation from the uploaded rows but does not save or replace the bundled evaluation dataset.

### Adjust settings

Open **Settings** to configure:

- The relative weights for skill overlap, experience, education/certifications, and keyword coverage. Entered weights are normalized to 100%; at least one must be non-zero. If a component is unknown for a candidate, the available components are rescaled for that candidate.
- spaCy entity extraction, or **Rule-based only** if you prefer not to use the spaCy model.
- Whether semantic similarity is enabled and which Sentence Transformers model name to use.
- Additional comma-separated skill terms for exact, case-insensitive matching. These terms apply to the current session; they do not have custom aliases or categories.

Settings apply to subsequent screenings in the current app session. Default weights and model names are in `config.py`.

### Privacy, logs, and decisions

The app processes uploads locally. It does not write resume text to the processing log. The log file `data/evaluation/screening_log.csv` records the uploaded filename, processing duration, success or failure, number of extracted skills, score, and a short error when applicable. Filenames and logs may still be sensitive; handle and remove them according to your organization's data practices. Do not upload documents unless you are authorized to process them.

Scores and suggestions are decision-support only. They are based on extracted text and a limited taxonomy, may be incomplete or incorrect, and must not be used as an automated hiring decision. A human should review the original application materials and relevant evidence.

### Common issues

- **`py` cannot find Python 3.11:** Check `py -0p`; install Python 3.10 or newer, then create the virtual environment with its launcher version.
- **`streamlit` or a Python module is not found:** Activate `.venv` and run `python -m pip install -r requirements.txt` again. Confirm `python --version` reports 3.10+.
- **spaCy model not found:** Run `python -m spacy download en_core_web_sm` in the same activated environment. Alternatively, select **Rule-based only** in Settings.
- **Scanned PDF has no readable text:** Install Tesseract and Poppler and confirm their executable directories are on `PATH`; restart the terminal and Streamlit afterward. If OCR cannot extract text, use a text-based PDF or DOCX instead.
- **Semantic similarity is unavailable:** Use TF-IDF, which is independent; disable semantic similarity in Settings or check model download/network access.
- **A candidate's result is missing after restart:** Session results are in memory, not persisted. Screen the resume again; export the results or download reports you want to keep.

## Sample data

Regenerate the original fictional datasets from the project root:

```text
python -m src.generate_sample_data
```

This writes 10 job-description text files, 25 mixed-format fictional resumes, a manifest, and 30 simulated evaluation pairs. Contact details use reserved `example.com` addresses and fictional 555 numbers. Generated evaluation ratings are illustrative labels, not human research or validated ground truth. For evaluation with actual reviewers, upload a CSV with `candidate_id`, `job_description_id`, `human_fit_rating` (1–5), and `screening_score`.

## Scoring methodology

The default component weights are skills 50%, experience 30%, education/certifications 10%, and keyword coverage 10%. Settings normalize user-entered weights to 100%. Mandatory skills receive twice the per-skill importance of preferred skills. Each available component is scaled to 0–100; missing evidence is shown as unknown and excluded from the weighted average, with remaining weights rescaled. A missing requirement is distinct from an unknown resume attribute.

TF-IDF cosine similarity and semantic similarity (when available) are displayed separately and are not conflated with the final match score. Final scores are explainable decision-support aids and can reflect extraction limitations; a human should review original materials and evidence before making decisions.

## Evaluation

The bundled evaluation set contains 30 candidate/job pairs with explicitly simulated 1–5 fit ratings. The app reports pair count, Spearman rank correlation, p-value, and a comparison plot when enough valid pairs are available. Replace demo labels with independent, consistently assigned human ratings before drawing conclusions. A correlation on synthetic examples is not evidence of real-world validity or fairness.

## Limitations

- Skill matching uses an editable vocabulary and conservative text patterns, not a complete ontology. Unlisted skills may be missed; broad terms can be ambiguous.
- Default spaCy NER is not relied on for technical skill detection. Job titles, degrees, and certifications are partly rule-based and may need human correction.
- Experience dates are estimates, do not account for overlapping roles or part-time work, and can be wrong if dates are ambiguous. Explicit total experience takes precedence when detected.
- OCR depends on local Tesseract and Poppler installations and may misread scanned content.
- Sentence Transformers requires a compatible runtime and may need network access for its initial model download.
- Demonstration data and fit labels are synthetic. Do not use the example correlation to make employment decisions.
- The tool is not validated for fairness, legal compliance, or autonomous candidate selection.

## Tests

Run the unit tests from the project root:

```text
python -m unittest discover -s tests -v
```

## Configuration and privacy

Set the optional `SPACY_MODEL` and `SEMANTIC_MODEL` environment variables shown in `.env.example` if you want different model defaults; Streamlit Settings can also change model behavior for the current session. No API key is required. Processing logs under `data/evaluation/screening_log.csv` include the candidate filename, duration, extraction outcome, extracted-skill count, score, and error detail; they do not contain the resume text. Treat logs and uploaded files as potentially sensitive and remove them when no longer needed.

## Future improvements

Potential next steps include user-reviewed entity corrections, structured interview and fairness evaluation workflows, more complete date overlap calculations, improved taxonomy coverage, and optional per-installation configuration of model-cache locations.
