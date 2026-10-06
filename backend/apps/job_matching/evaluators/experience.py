"""
apps/job_matching/evaluators/experience.py

ExperienceEvaluator — Weight: 20 points.

Compares required experience years against candidate experience.
Handles:
  - Required years vs candidate total years
  - Freshers & entry-level roles (no zero score penalty)
  - Internships count positively
"""
from typing import Dict, Any, List

from ..constants import WEIGHTS


class ExperienceEvaluator:
    """
    Evaluates experience match between resume and job description.

    Responsibility:
        Calculate experience score out of 20 based on required years vs
        candidate experience entries.
    """

    WEIGHT: int = WEIGHTS["experience"]

    def evaluate(
        self,
        resume_experience: List[Dict[str, Any]],
        required_years: float,
    ) -> Dict[str, Any]:
        """
        Evaluate experience match.

        Args:
            resume_experience: List of experience dicts from ParsedResume.
            required_years: Float required years of experience from JD.

        Returns:
            Dict containing:
                - score: float (0 to 20)
                - max_score: 20
                - candidate_years_est: float
                - is_fresher_friendly: bool
        """
        max_score = self.WEIGHT

        # Estimate candidate total years from experience entries count & bullets
        num_entries = len(resume_experience or [])
        candidate_years_est = num_entries * 1.5  # standard estimation

        has_internship = False
        for entry in resume_experience or []:
            title = (entry.get("title") or "").lower()
            company = (entry.get("company") or "").lower()
            if "intern" in title or "intern" in company:
                has_internship = True

        # Case A: JD requires 0 years (Fresher / Entry Level)
        if required_years == 0:
            score = max_score  # Everyone qualifies for fresher roles
            return {
                "score": score,
                "max_score": max_score,
                "candidate_years_est": candidate_years_est,
                "is_fresher_friendly": True,
                "detail": "Role is fresher/entry level — candidate meets experience requirement.",
            }

        # Case B: Candidate has no experience listed
        if num_entries == 0:
            # If JD requires 1-2 years, give partial 5 points; if >3 years, give 2 points
            score = 5 if required_years <= 2 else 2
            return {
                "score": score,
                "max_score": max_score,
                "candidate_years_est": 0.0,
                "is_fresher_friendly": False,
                "detail": f"Job requires {required_years} year(s); candidate lists 0 years.",
            }

        # Case C: Candidate has experience
        if candidate_years_est >= required_years:
            score = max_score
        else:
            # Candidate has partial experience
            ratio = candidate_years_est / required_years
            base = ratio * max_score
            if has_internship:
                base += 2.0  # Internship bonus
            score = min(base, max_score)

        return {
            "score": round(score, 1),
            "max_score": max_score,
            "candidate_years_est": candidate_years_est,
            "is_fresher_friendly": False,
            "detail": f"Candidate has ~{candidate_years_est} year(s); JD requires {required_years} year(s).",
        }
