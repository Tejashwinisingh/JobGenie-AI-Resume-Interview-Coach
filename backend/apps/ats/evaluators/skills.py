"""
apps/ats/evaluators/skills.py

SkillsEvaluator — Weight: 15 points.

Evaluates the skills section from structured parsed data:
  - Number of technical skills listed
  - Variety (avoids duplicate-heavy lists)
  - Rewards breadth across categories
"""
from typing import Dict, Any, List

from ..constants import WEIGHTS, TECHNICAL_SKILLS


class SkillsEvaluator:
    """
    Evaluates the quality and quantity of skills in the parsed resume.

    Responsibility:
        Score the parsed skills list for count, variety, and relevance
        without considering the raw resume text directly.
    """

    WEIGHT: int = WEIGHTS["skills"]

    def evaluate(self, skills: List[str]) -> Dict[str, Any]:
        """
        Score the parsed skills list.

        Args:
            skills: List of skill strings from ParsedResume.skills.

        Returns:
            Dict with score, max_score, warnings, details.
        """
        max_score = self.WEIGHT
        score = 0
        warnings: List[str] = []

        if not skills:
            return {
                "score": 0,
                "max_score": max_score,
                "warnings": [
                    "No skills were detected in the resume. "
                    "Add a dedicated Skills section with relevant technologies."
                ],
                "details": {"total_skills": 0, "unique_skills": 0, "categories_covered": 0},
            }

        # Deduplicate (case-insensitive)
        unique_skills = list({s.lower(): s for s in skills}.values())
        total = len(unique_skills)
        duplicate_count = len(skills) - total

        if duplicate_count > 0:
            warnings.append(f"{duplicate_count} duplicate skill(s) found — remove duplicates.")

        # ── Count scoring (0–9 points) ────────────────────────────────────
        if total >= 20:
            score += 9
        elif total >= 15:
            score += 8
        elif total >= 10:
            score += 7
        elif total >= 7:
            score += 5
        elif total >= 4:
            score += 3
        elif total >= 1:
            score += 2
            warnings.append(
                f"Only {total} skill(s) detected. Consider listing at least 8–10 skills."
            )

        # ── Category variety scoring (0–6 points) ─────────────────────────
        skills_lower = {s.lower() for s in unique_skills}
        categories_covered = 0
        for category, cat_skills in TECHNICAL_SKILLS.items():
            cat_lower = {k.lower() for k in cat_skills}
            if skills_lower & cat_lower:  # intersection
                categories_covered += 1

        if categories_covered >= 5:
            score += 6
        elif categories_covered >= 4:
            score += 5
        elif categories_covered >= 3:
            score += 4
        elif categories_covered >= 2:
            score += 3
        elif categories_covered >= 1:
            score += 2
        else:
            score += 0
            warnings.append(
                "No recognizable technical category skills found. "
                "List skills from languages, frameworks, databases, or cloud tools."
            )

        if categories_covered < 3:
            warnings.append(
                f"Skills span only {categories_covered} technical area(s). "
                "Diversify across languages, frameworks, databases, and tools."
            )

        return {
            "score": min(score, max_score),
            "max_score": max_score,
            "warnings": warnings,
            "details": {
                "total_skills": total,
                "unique_skills": total,
                "duplicate_count": duplicate_count,
                "categories_covered": categories_covered,
            },
        }
