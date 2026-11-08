import unittest

from src.report_generator import generate_pdf_report
from src.screening import screen_candidate


class ReportGeneratorTests(unittest.TestCase):
    def test_candidate_report_is_a_pdf(self):
        resume_text = (
            "Avery Morgan\nSummary\nPython developer\n"
            "Technical Skills\nPython, Django, PostgreSQL\n"
            "Education\nBachelor of Science in Computer Science"
        )
        result = screen_candidate(
            {"filename": "candidate.pdf", "text": resume_text},
            "Job Title: Python Developer\nMandatory Skills\n- Python\n- Django",
            enable_semantic=False,
            spacy_model="Rule-based only",
        )
        report = generate_pdf_report(result)
        self.assertTrue(report.startswith(b"%PDF-"))


if __name__ == "__main__":
    unittest.main()
