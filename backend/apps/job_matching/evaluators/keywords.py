"""
apps/job_matching/evaluators/keywords.py

KeywordsEvaluator — Weight: 10 points.

Compares domain keywords between Job Description text and Resume text.
Calculates:
  - Matched Keywords
  - Missing Keywords
  - Keyword Score (out of 10)
"""
from typing import Dict, Any, List, Set

from ..constants import WEIGHTS
from ..utils import extract_keywords_from_text


class KeywordsEvaluator:
    """
    Evaluates keyword overlap between JD text and resume text.

    Responsibility:
        Calculate technical keyword overlap out of 10.
    """

    WEIGHT: int = WEIGHTS["keywords"]

    def evaluate(
        self,
        resume_text: str,
        jd_text: str,
    ) -> Dict[str, Any]:
        """
        Evaluate keyword match.

        Args:
            resume_text: Cleaned text of candidate resume.
            jd_text: Cleaned text of job description.

        Returns:
            Dict containing:
                - score: float (0 to 10)
                - max_score: 10
                - matched_keywords: List[str]
                - missing_keywords: List[str]
        """
        max_score = self.WEIGHT

        res_kw: Set[str] = extract_keywords_from_text(resume_text or "")
        jd_kw: Set[str] = extract_keywords_from_text(jd_text or "")

        if not jd_kw:
            return {
                "score": max_score,
                "max_score": max_score,
                "matched_keywords": [],
                "missing_keywords": [],
            }

        matched = res_kw & jd_kw
        missing = jd_kw - res_kw

        ratio = len(matched) / len(jd_kw) if jd_kw else 1.0
        score = min(ratio * max_score * 1.5, max_score)  # 66% keyword overlap gives full score

        return {
            "score": round(score, 1),
            "max_score": max_score,
            "matched_keywords": sorted(list(matched))[:15],
            "missing_keywords": sorted(list(missing))[:15],
        }
