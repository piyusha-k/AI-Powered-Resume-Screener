import unittest

from src.matcher import analyze_match, similarity_scores
from src.nlp_engine import extract_job_requirements


class MatcherTests(unittest.TestCase):
    def test_missing_and_matched_skills_are_normalized(self):
        result = analyze_match(
            {"text": "Technical Skills\nJS, ReactJS, PostgreSQL"},
            {"required_skills": ["JavaScript", "React", "Python"], "preferred_skills": ["SQL"]},
        )
        self.assertEqual(result["matched_required_skills"], ["JavaScript", "React"])
        self.assertEqual(result["missing_required_skills"], ["Python"])
        self.assertEqual(result["matched_preferred_skills"], [])

    def test_tfidf_similarity_is_bounded(self):
        result = similarity_scores("Python developer with Django", "Python and Django developer")
        self.assertGreaterEqual(result["tfidf"], 0.0)
        self.assertLessEqual(result["tfidf"], 1.0)

    def test_semantic_similarity_can_be_disabled(self):
        result = similarity_scores("Python developer", "Python engineer", enable_semantic=False)
        self.assertIsNone(result["semantic"])

    def test_only_explicit_job_skill_sections_are_classified(self):
        job = extract_job_requirements(
            "Responsibilities\n- Use Python daily\nPreferred Skills\n- Docker"
        )
        self.assertEqual(job["required_skills"], [])
        self.assertEqual(job["preferred_skills"], ["Docker"])

    def test_custom_skill_is_used_for_requirement_and_resume_matching(self):
        job = extract_job_requirements(
            "Mandatory Skills\n- GraphQL",
            additional_skills=["GraphQL"],
        )
        result = analyze_match(
            {"text": "Used GraphQL to build a project API."},
            job,
            additional_skills=["GraphQL"],
        )
        self.assertEqual(result["matched_required_skills"], ["GraphQL"])


if __name__ == "__main__":
    unittest.main()
