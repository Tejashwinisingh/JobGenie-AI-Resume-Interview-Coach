"""
apps/ats/scoring.py

ATSScorer — Pure, stateless scoring utilities.

Responsible only for:
  - Computing the letter grade from a numeric score
  - Generating a human-readable summary sentence
  - Summing a breakdown dict into a total score
"""
from typing import Dict, Tuple

from .constants import GRADE_THRESHOLDS


class ATSScorer:
    """
    Pure scoring utilities for the ATS Engine.

    All methods are static — no state, no side effects.
    Independently testable without any DB or model dependencies.
    """

    @staticmethod
    def compute_grade(score: int) -> Tuple[str, str]:
        """
        Return (grade_letter, grade_label) for a given numeric score.

        Args:
            score: Integer ATS score (0–100).

        Returns:
            Tuple of (grade: str, label: str).

        Example:
            compute_grade(85) → ("A", "Very Good")
        """
        for threshold, grade, label in GRADE_THRESHOLDS:
            if score >= threshold:
                return grade, label
        return "D", "Needs Improvement"

    @staticmethod
    def compute_summary(score: int, grade: str, label: str) -> str:
        """
        Generate a concise human-readable ATS summary sentence.

        Args:
            score: Integer ATS score.
            grade: Letter grade (e.g. "A+").
            label: Grade label (e.g. "Excellent").

        Returns:
            A summary string.
        """
        if score >= 90:
            return (
                f"Outstanding ATS-friendly resume (Grade {grade}). "
                "This resume will pass most ATS filters with high confidence."
            )
        elif score >= 80:
            return (
                f"Very well-structured, ATS-friendly resume (Grade {grade}). "
                "Minor improvements can push it to excellent."
            )
        elif score >= 70:
            return (
                f"Good ATS compatibility (Grade {grade}). "
                "A few important areas need attention to improve pass rate."
            )
        elif score >= 60:
            return (
                f"Average ATS compatibility (Grade {grade}). "
                "Several key areas are missing or underdeveloped."
            )
        else:
            return (
                f"Low ATS compatibility (Grade {grade}). "
                "Significant improvements needed in structure, keywords, and sections."
            )

    @staticmethod
    def compute_total(breakdown: Dict[str, int]) -> int:
        """
        Sum all category scores in a breakdown dict.

        Args:
            breakdown: Dict mapping category names to integer scores.

        Returns:
            Total integer score (capped at 100).
        """
        return min(sum(breakdown.values()), 100)
