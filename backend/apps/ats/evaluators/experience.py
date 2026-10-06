"""
apps/ats/evaluators/experience.py

ExperienceEvaluator — Weight: 10 points.

Evaluates work experience from parsed resume data.
Key design: Freshers and interns are NOT penalised — internships,
academic projects, and training count positively.
"""
import re
from typing import Dict, Any, List

from ..constants import WEIGHTS


class ExperienceEvaluator:
    """
    Evaluates professional experience from parsed resume data.

    Responsibility:
        Score work experience entries for role, company, duration,
        and description quality. Freshers and interns score positively.
    """

    WEIGHT: int = WEIGHTS["experience"]

    INTERNSHIP_KEYWORDS = [
        "intern", "internship", "trainee", "apprentice",
        "industrial training", "summer project", "co-op",
    ]

    def evaluate(self, experience: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Score the parsed experience list.

        Args:
            experience: List of experience dicts from ParsedResume.experience.
                        Each may have: title, company, date, bullets.

        Returns:
            Dict with score, max_score, warnings, details.
        """
        max_score = self.WEIGHT
        score = 0
        warnings: List[str] = []
        is_fresher = False

        if not experience:
            warnings.append(
                "No work experience detected. If you are a fresher, "
                "list internships, academic projects, or training."
            )
            is_fresher = True
            # Freshers get base score; no zero penalty
            return {
                "score": 2,
                "max_score": max_score,
                "warnings": warnings,
                "details": {"entries": 0, "is_fresher": True},
            }

        total_score = 0
        has_internship = False

        for entry in experience:
            entry_score = 0
            title = (entry.get("title") or "").strip()
            company = (entry.get("company") or "").strip()
            date_str = (entry.get("date") or "").strip()
            bullets = entry.get("bullets") or []

            # Check if it's an internship
            combined = f"{title} {company}".lower()
            if any(kw in combined for kw in self.INTERNSHIP_KEYWORDS):
                has_internship = True

            # Role/title present (2 points)
            if title:
                entry_score += 2
            else:
                warnings.append("Job title/role is missing from an experience entry.")

            # Company present (2 points)
            if company:
                entry_score += 2
            else:
                warnings.append("Company name is missing from an experience entry.")

            # Duration/date present (2 points)
            if date_str:
                years_found = re.findall(r"\b(19|20)\d{2}\b", date_str)
                if years_found:
                    entry_score += 2
                else:
                    entry_score += 1
                    warnings.append(
                        "Dates in experience entry do not include a year."
                    )
            else:
                warnings.append("No dates found in an experience entry.")

            # Responsibilities/bullets (2 points)
            if bullets and len(bullets) >= 2:
                entry_score += 2
            elif bullets and len(bullets) == 1:
                entry_score += 1
                warnings.append(
                    "Experience entry has only one responsibility bullet. "
                    "Add more detail for ATS confidence."
                )

            total_score = max(total_score, entry_score)

        # Multiple experience entries bonus
        if len(experience) > 1:
            total_score = min(total_score + 2, max_score)

        if has_internship and len(experience) == 1:
            # Single internship: ensure at least partial score
            total_score = max(total_score, 4)
            warnings.append(
                "Only internship experience found — that's great for freshers! "
                "Consider adding more internships or projects."
            )

        score = min(total_score, max_score)

        return {
            "score": score,
            "max_score": max_score,
            "warnings": list(dict.fromkeys(warnings)),
            "details": {
                "entries": len(experience),
                "has_internship": has_internship,
                "is_fresher": is_fresher,
            },
        }
