"""
apps/ats/evaluators/education.py

EducationEvaluator — Weight: 10 points.

Evaluates education entries from parsed resume data:
  - Degree is present
  - Institution is present
  - Graduation year is present
  - CGPA/GPA mentioned (optional bonus)
"""
import re
from typing import Dict, Any, List

from ..constants import WEIGHTS


class EducationEvaluator:
    """
    Evaluates education section from parsed resume data.

    Responsibility:
        Score the structured education list for completeness
        (degree, institution, year) without touching raw text.
    """

    WEIGHT: int = WEIGHTS["education"]

    # Degree-level keywords for recognition
    DEGREE_KEYWORDS = [
        "bachelor", "b.e", "b.tech", "be", "btech", "b.sc", "bsc",
        "master", "m.e", "m.tech", "me", "mtech", "m.sc", "msc", "mba",
        "phd", "ph.d", "doctorate", "diploma", "associate", "b.com", "bcom",
        "b.ca", "bca", "engineering", "degree",
    ]

    def evaluate(self, education: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Score the parsed education list.

        Args:
            education: List of education dicts from ParsedResume.education.
                       Each dict may have: degree, institution, date, gpa.

        Returns:
            Dict with score, max_score, warnings, details.
        """
        max_score = self.WEIGHT
        score = 0
        warnings: List[str] = []

        if not education:
            return {
                "score": 0,
                "max_score": max_score,
                "warnings": [
                    "No education information detected. "
                    "Add an Education section with degree, institution, and graduation year."
                ],
                "details": {"entries": 0},
            }

        best_score = 0

        for entry in education:
            entry_score = 0
            degree = (entry.get("degree") or "").strip()
            institution = (entry.get("institution") or "").strip()
            date_str = (entry.get("date") or "").strip()

            # Degree present (4 points)
            if degree:
                entry_score += 4
                # Bonus if it's a recognisable degree type
                deg_lower = degree.lower()
                if any(kw in deg_lower for kw in self.DEGREE_KEYWORDS):
                    entry_score += 1  # Will be capped
            else:
                warnings.append("Degree name is missing from an education entry.")

            # Institution present (3 points)
            if institution:
                entry_score += 3
            else:
                warnings.append("Institution name is missing from an education entry.")

            # Graduation year present (2 points)
            year_found = bool(re.search(r"\b(19|20)\d{2}\b", date_str))
            if year_found:
                entry_score += 2
            else:
                warnings.append(
                    "Graduation year not detected in education entry. "
                    "Include the year (e.g. 2024)."
                )

            # GPA/CGPA optional (1 bonus point)
            gpa = (entry.get("gpa") or "").strip()
            if gpa:
                entry_score += 1

            best_score = max(best_score, entry_score)

        score = min(best_score, max_score)

        if len(education) > 1:
            # Multiple education entries slightly boost confidence
            score = min(score + 1, max_score)

        return {
            "score": score,
            "max_score": max_score,
            "warnings": list(dict.fromkeys(warnings)),  # deduplicate
            "details": {"entries": len(education)},
        }
