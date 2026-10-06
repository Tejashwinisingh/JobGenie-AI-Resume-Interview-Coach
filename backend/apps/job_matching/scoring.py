"""
apps/job_matching/scoring.py

JobMatchingScorer — Pure scoring utilities.

Calculates grade letter/label and total score for Job Description matching.
"""
from typing import Dict, Tuple

from .constants import GRADE_THRESHOLDS


class JobMatchingScorer:
    """
    Pure scoring utilities for Job Description matching.
    """

    @staticmethod
    def compute_grade(score: int) -> Tuple[str, str]:
        """
        Return (grade_letter, grade_label) for a given match score.

        Args:
            score: Integer match score (0–100).

        Returns:
            Tuple of (grade: str, label: str).
        """
        for threshold, grade, label in GRADE_THRESHOLDS:
            if score >= threshold:
                return grade, label
        return "D", "Needs Improvement"

    @staticmethod
    def compute_total(breakdown: Dict[str, float]) -> int:
        """
        Sum category scores and round to integer (max 100).
        """
        total = sum(breakdown.values())
        return min(round(total), 100)
