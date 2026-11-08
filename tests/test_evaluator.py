import unittest

import pandas as pd

from src.evaluator import evaluate_pairs


class EvaluatorTests(unittest.TestCase):
    def test_spearman_uses_valid_pairs_and_reports_count(self):
        result = evaluate_pairs(pd.DataFrame({
            "human_fit_rating": [1, 2, 3, 4],
            "screening_score": [10, 30, 50, 90],
        }))
        self.assertEqual(result["pair_count"], 4)
        self.assertAlmostEqual(result["coefficient"], 1.0)

    def test_out_of_range_ratings_are_rejected(self):
        with self.assertRaises(ValueError):
            evaluate_pairs(pd.DataFrame({
                "human_fit_rating": [1, 6],
                "screening_score": [20, 80],
            }))

    def test_constant_scores_have_no_correlation(self):
        result = evaluate_pairs(pd.DataFrame({
            "human_fit_rating": [2, 4, 5],
            "screening_score": [50, 50, 50],
        }))
        self.assertIsNone(result["coefficient"])
        self.assertIsNone(result["p_value"])


if __name__ == "__main__":
    unittest.main()
