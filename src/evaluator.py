"""Evaluation helpers for clearly labeled simulated ratings and human review data."""

from pathlib import Path
from typing import Any, Dict

import pandas as pd
from scipy.stats import spearmanr


def evaluate_pairs(data: pd.DataFrame) -> Dict[str, Any]:
    """Compute Spearman correlation for valid human-rating / screening-score pairs."""
    required = {"human_fit_rating", "screening_score"}
    if not required.issubset(data.columns):
        raise ValueError("Evaluation CSV must include human_fit_rating and screening_score.")
    frame = data.copy()
    frame["human_fit_rating"] = pd.to_numeric(frame["human_fit_rating"], errors="coerce")
    frame["screening_score"] = pd.to_numeric(frame["screening_score"], errors="coerce")
    frame = frame.dropna(subset=["human_fit_rating", "screening_score"])
    if not frame.empty and not frame["human_fit_rating"].between(1, 5).all():
        raise ValueError("Human fit ratings must use the 1–5 scale.")
    if len(frame) < 2:
        return {"coefficient": None, "p_value": None, "pair_count": len(frame), "pairs": frame}
    if frame["human_fit_rating"].nunique() < 2 or frame["screening_score"].nunique() < 2:
        return {"coefficient": None, "p_value": None, "pair_count": len(frame), "pairs": frame}
    result = spearmanr(frame["human_fit_rating"], frame["screening_score"])
    return {
        "coefficient": float(result.statistic),
        "p_value": float(result.pvalue),
        "pair_count": len(frame),
        "pairs": frame,
    }


def load_evaluation_data(path: Path) -> pd.DataFrame:
    """Load CSV evaluation data, clearly exposing the synthetic-label disclaimer."""
    if not path.exists():
        raise FileNotFoundError("Evaluation CSV was not found: {0}".format(path))
    return pd.read_csv(path)
