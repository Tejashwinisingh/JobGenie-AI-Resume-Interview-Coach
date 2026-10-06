"""
apps/ats/evaluators/structure.py

StructureEvaluator — Weight: 10 points.

Evaluates whether standard ATS-expected section headings are present in the
resume text. Missing or creatively named sections reduce the score.
"""
from typing import Dict, Any, List

from ..constants import WEIGHTS, SECTION_HEADINGS
from ..utils import find_section_in_text


class StructureEvaluator:
    """
    Evaluates presence of standard ATS section headings.

    Responsibility:
        Detect whether the resume contains expected sections such as
        Skills, Education, Experience, Projects, Summary, etc.
    """

    WEIGHT: int = WEIGHTS["structure"]

    # Sections and their individual point contributions (must sum to WEIGHT=10)
    SECTION_WEIGHTS: Dict[str, int] = {
        "skills":         2,
        "education":      2,
        "experience":     2,
        "projects":       1,
        "summary":        1,
        "certifications": 1,
        "achievements":   1,
    }

    def evaluate(self, cleaned_text: str) -> Dict[str, Any]:
        """
        Scan resume text for standard section headings.

        Args:
            cleaned_text: Cleaned resume text from Module 3.

        Returns:
            Dict with keys: score, max_score, warnings, details,
                            found_sections, missing_sections.
        """
        max_score = self.WEIGHT
        score = 0
        warnings: List[str] = []
        found_sections: List[str] = []
        missing_sections: List[str] = []
        details: Dict[str, bool] = {}

        text = cleaned_text or ""

        for section_key, points in self.SECTION_WEIGHTS.items():
            aliases = SECTION_HEADINGS.get(section_key, [])
            found, matched = find_section_in_text(aliases, text)
            details[section_key] = found

            if found:
                score += points
                found_sections.append(section_key.title())
            else:
                missing_sections.append(section_key.title())
                if points >= 2:
                    warnings.append(
                        f'Important section "{section_key.title()}" was not detected. '
                        "ATS systems require clearly labelled sections."
                    )
                else:
                    warnings.append(
                        f'Optional section "{section_key.title()}" is missing.'
                    )

        return {
            "score": min(score, max_score),
            "max_score": max_score,
            "warnings": warnings,
            "details": details,
            "found_sections": found_sections,
            "missing_sections": missing_sections,
        }
