import unittest

from src.taxonomy import extract_skills, normalize_skill


class TaxonomyTests(unittest.TestCase):
    def test_aliases_normalize(self):
        self.assertEqual(normalize_skill("JS"), "JavaScript")
        self.assertEqual(normalize_skill("Postgres"), "PostgreSQL")
        self.assertEqual(normalize_skill("NLP"), "Natural Language Processing")

    def test_extract_skills_uses_boundaries_and_disambiguates_spring(self):
        self.assertNotIn("Java", extract_skills("I enjoy javascript"))
        self.assertNotIn("Spring Framework", extract_skills("Spring is a season."))
        self.assertIn("Spring Framework", extract_skills("Built services with Spring Boot."))

    def test_custom_taxonomy_terms_match_case_insensitively(self):
        self.assertEqual(extract_skills("Using graphQL APIs", ["GraphQL"]), ["GraphQL"])


if __name__ == "__main__":
    unittest.main()
