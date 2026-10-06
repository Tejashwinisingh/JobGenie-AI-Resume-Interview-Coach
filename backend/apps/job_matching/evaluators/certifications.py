"""
apps/job_matching/evaluators/certifications.py

CertificationsEvaluator — Weight: 10 points.

Compares required professional certifications against candidate certifications.
"""
from typing import Dict, Any, List, Set

from ..constants import WEIGHTS


class CertificationsEvaluator:
    """
    Evaluates certification match between resume and job description.

    Responsibility:
        Score certification overlap out of 10.
    """

    WEIGHT: int = WEIGHTS["certifications"]

    def evaluate(
        self,
        resume_certifications: List[Any],
        required_certifications: List[str],
    ) -> Dict[str, Any]:
        """
        Evaluate certification match.

        Args:
            resume_certifications: List of cert dicts or strings from ParsedResume.
            required_certifications: List of required cert strings from JD.

        Returns:
            Dict containing:
                - score: float (0 to 10)
                - max_score: 10
                - matched_certifications: List[str]
                - missing_certifications: List[str]
        """
        max_score = self.WEIGHT

        # Normalize candidate certs
        res_certs: Set[str] = set()
        for item in resume_certifications or []:
            if isinstance(item, dict):
                name = item.get("name") or ""
            else:
                name = str(item)
            if name.strip():
                res_certs.add(name.lower().strip())

        req_certs: Set[str] = {c.lower().strip() for c in (required_certifications or []) if c.strip()}

        if not req_certs:
            # If JD requires no specific certifications → base score on having certs
            score = max_score if res_certs else 8
            return {
                "score": score,
                "max_score": max_score,
                "matched_certifications": sorted([c.title() for c in res_certs]),
                "missing_certifications": [],
            }

        matched = res_certs & req_certs
        missing = req_certs - res_certs

        ratio = len(matched) / len(req_certs)
        score = ratio * max_score

        return {
            "score": round(score, 1),
            "max_score": max_score,
            "matched_certifications": sorted([c.title() for c in matched]),
            "missing_certifications": sorted([c.title() for c in missing]),
        }
