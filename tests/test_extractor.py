import unittest
from pathlib import Path

from config import SAMPLE_RESUMES_DIR
from src.extractor import extract_document, extract_file
from src.preprocessor import detect_sections


class ExtractorTests(unittest.TestCase):
    def test_txt_job_description_is_cleaned_and_sectioned(self):
        result = extract_document(
            "role.txt",
            b"Job overview\n\nPython developer\n\nEducation\nBSc Computer Science",
            document_kind="job",
        )
        self.assertIn("Python developer", result["text"])
        self.assertIn("education", result["sections"])

    def test_invalid_file_type_is_rejected(self):
        with self.assertRaises(ValueError):
            extract_document("resume.exe", b"not a resume")

    def test_resume_sections_are_detected(self):
        sections = detect_sections("Summary\nEngineer\n\nTechnical Skills\nPython, Django")
        self.assertEqual(sections["technical_skills"], "Python, Django")

    def test_synthetic_pdf_and_docx_resumes_are_readable(self):
        for suffix in (".pdf", ".docx"):
            path = next(SAMPLE_RESUMES_DIR.glob("*" + suffix))
            result = extract_file(path, enable_ocr=False)
            self.assertGreaterEqual(len(result["text"]), 20)
            self.assertIn("work_experience", result["sections"])


if __name__ == "__main__":
    unittest.main()
