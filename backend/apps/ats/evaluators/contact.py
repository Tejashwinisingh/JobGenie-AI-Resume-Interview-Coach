"""
apps/ats/evaluators/contact.py

ContactEvaluator — Weight: 10 points.

Evaluates the completeness of contact information on the resume.
Each field (name, email, phone, LinkedIn, GitHub) contributes equally.
"""
from typing import Dict, Any

from ..constants import WEIGHTS


class ContactEvaluator:
    """
    Evaluates contact information completeness.

    Responsibility:
        Check for presence of name, email, phone, LinkedIn, and GitHub
        in the parsed resume data and score accordingly.
    """

    WEIGHT: int = WEIGHTS["contact"]

    # Points per field
    FIELD_SCORES: Dict[str, int] = {
        "name":     3,
        "email":    3,
        "phone":    2,
        "linkedin": 1,
        "github":   1,
    }

    def evaluate(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Score contact information based on parsed resume fields.

        Args:
            parsed_data: Dict from ParsedResume (name, email, phone, linkedin, github).

        Returns:
            Dict with keys: score, max_score, warnings, details.
        """
        max_score = self.WEIGHT
        score = 0
        warnings = []
        details: Dict[str, bool] = {}

        for field, points in self.FIELD_SCORES.items():
            value = (parsed_data.get(field) or "").strip()
            if value:
                score += points
                details[field] = True
            else:
                details[field] = False
                label = field.capitalize()
                warnings.append(f"{label} is missing from the resume.")

        return {
            "score": min(score, max_score),
            "max_score": max_score,
            "warnings": warnings,
            "details": details,
        }
