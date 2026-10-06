"""
apps/ats/evaluators/projects.py

ProjectsEvaluator — Weight: 5 points.

Evaluates project entries from parsed resume data:
  - Project title present
  - Description present
  - Technologies used mentioned
  - Multiple projects increase confidence
"""
from typing import Dict, Any, List

from ..constants import WEIGHTS


class ProjectsEvaluator:
    """
    Evaluates the projects section from parsed resume data.

    Responsibility:
        Score project entries for title, description, and technology
        mentions. Rewards multiple well-described projects.
    """

    WEIGHT: int = WEIGHTS["projects"]

    def evaluate(self, projects: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Score the parsed projects list.

        Args:
            projects: List of project dicts from ParsedResume.projects.
                      Each may have: title, description, technologies.

        Returns:
            Dict with score, max_score, warnings, details.
        """
        max_score = self.WEIGHT
        score = 0
        warnings: List[str] = []

        if not projects:
            warnings.append(
                "No projects detected. Add a Projects section with at least "
                "2–3 projects including technologies used."
            )
            return {
                "score": 0,
                "max_score": max_score,
                "warnings": warnings,
                "details": {"entries": 0},
            }

        quality_projects = 0

        for proj in projects:
            title = (proj.get("title") or "").strip()
            description = (proj.get("description") or "").strip()
            technologies = proj.get("technologies") or []

            proj_quality = 0

            if title:
                proj_quality += 1
            else:
                warnings.append("A project entry is missing a title.")

            if description and len(description) > 20:
                proj_quality += 1
            elif description:
                proj_quality += 1
                warnings.append(
                    f'Project "{title or "Unnamed"}" has a very short description.'
                )
            else:
                warnings.append(
                    f'Project "{title or "Unnamed"}" is missing a description.'
                )

            if technologies:
                proj_quality += 1
            else:
                warnings.append(
                    f'Technologies used not specified for project "{title or "Unnamed"}".'
                )

            if proj_quality == 3:
                quality_projects += 1

        # Scoring tiers based on quality project count
        if quality_projects >= 3:
            score = 5
        elif quality_projects >= 2:
            score = 4
        elif quality_projects >= 1:
            score = 3
        elif len(projects) >= 1:
            # Projects exist but incomplete
            score = 2
            warnings.append(
                "Projects section needs more detail (add descriptions and technologies)."
            )

        if len(projects) < 2:
            warnings.append(
                f"Only {len(projects)} project(s) found. "
                "Include 2–3 projects to strengthen ATS score."
            )

        return {
            "score": min(score, max_score),
            "max_score": max_score,
            "warnings": list(dict.fromkeys(warnings)),
            "details": {
                "entries": len(projects),
                "quality_projects": quality_projects,
            },
        }
