"""
apps/job_matching/evaluators/education.py

EducationEvaluator — Weight: 10 points.

Compares required degree against candidate education entries.
Returns:
  - Match Status: "Full Match", "Partial Match", "No Match"
  - Education Score (out of 10)
"""
from typing import Dict, Any, List

from ..constants import WEIGHTS
from ..utils import match_degree_level


class EducationEvaluator:
    """
    Evaluates education match between resume and job description.

    Responsibility:
        Score candidate degree against JD required degree.
    """

    WEIGHT: int = WEIGHTS["education"]

    def evaluate(
        self,
        resume_education: List[Dict[str, Any]],
        required_degree: str,
    ) -> Dict[str, Any]:
        """
        Evaluate education match.

        Args:
            resume_education: List of education dicts from ParsedResume.
            required_degree: Required degree string from ParsedJobDescription.

        Returns:
            Dict containing:
                - score: float (0 to 10)
                - max_score: 10
                - match_status: str ("Full Match", "Partial Match", "No Match")
                - candidate_degree: str
                - required_degree: str
        """
        max_score = self.WEIGHT

        if not required_degree:
            # If JD specifies no degree requirement → full score
            return {
                "score": max_score,
                "max_score": max_score,
                "match_status": "Full Match",
                "candidate_degree": "N/A",
                "required_degree": "None specified",
            }

        if not resume_education:
            # Candidate has no education listed
            return {
                "score": 0,
                "max_score": max_score,
                "match_status": "No Match",
                "candidate_degree": "None listed",
                "required_degree": required_degree,
            }

        # Check candidate's best degree match
        best_score = 0.0
        best_status = "No Match"
        candidate_deg_name = ""

        for edu in resume_education:
            deg = (edu.get("degree") or "").strip()
            status_str, ratio = match_degree_level(required_degree, deg)
            points = ratio * max_score
            if points > best_score:
                best_score = points
                best_status = status_str
                candidate_deg_name = deg

        return {
            "score": round(best_score, 1),
            "max_score": max_score,
            "match_status": best_status,
            "candidate_degree": candidate_deg_name or "Listed",
            "required_degree": required_degree,
        }
