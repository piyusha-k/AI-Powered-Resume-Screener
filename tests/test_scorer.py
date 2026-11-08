import unittest

from config import DEFAULT_SCORING_WEIGHTS
from src.matcher import analyze_match
from src.scorer import calculate_scores, normalize_weights
from src.screening import screen_candidate
from src.taxonomy import extract_skills


class ScorerTests(unittest.TestCase):
    def test_weights_are_normalized_to_one_hundred(self):
        weights = normalize_weights({"skills": 30, "experience": 30, "education_certifications": 20,
                                     "keyword_coverage": 20})
        self.assertAlmostEqual(sum(weights.values()), 100.0)
        self.assertAlmostEqual(sum(normalize_weights(DEFAULT_SCORING_WEIGHTS).values()), 100.0)

    def test_final_score_stays_in_range(self):
        text = "Avery Morgan\nTechnical Skills\nPython, Django, PostgreSQL\n5 years of experience"
        job = {"required_skills": ["Python", "Django"], "preferred_skills": ["AWS"],
               "required_experience_years": 3, "education_requirements": [], "certification_requirements": [],
               "all_skills": ["Python", "Django", "AWS"]}
        match = analyze_match({"text": text}, job)
        entities = {"experience": {"years": 5}, "degrees": [], "certifications": []}
        result = calculate_scores(match, entities, job, text)
        self.assertGreaterEqual(result["final_score"], 0)
        self.assertLessEqual(result["final_score"], 100)

    def test_unreadable_resume_is_not_scored(self):
        with self.assertRaises(ValueError):
            screen_candidate({"text": ""}, "Python developer")

    def test_missing_education_section_is_unknown_not_a_gap(self):
        text = "Avery Morgan\nPython developer"
        job = {"required_skills": ["Python"], "preferred_skills": [],
               "required_experience_years": None,
               "education_requirements": ["Bachelor's degree"],
               "certification_requirements": [], "all_skills": ["Python"]}
        match = analyze_match({"text": text}, job)
        result = calculate_scores(
            match,
            {"experience": {"years": None}, "degrees": [], "certifications": []},
            job,
            text,
        )
        self.assertIsNone(result["components"]["education_certifications"])
        self.assertIn("education_certifications", result["unknown_components"])

    def test_extracted_skills_are_nonempty_for_known_terms(self):
        self.assertEqual(extract_skills("Django and PostgreSQL"), ["Django", "PostgreSQL"])


if __name__ == "__main__":
    unittest.main()
