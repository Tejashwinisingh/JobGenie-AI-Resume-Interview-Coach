"""
apps/job_matching/evaluators/skills.py

SkillsEvaluator — Weight: 50 points.

Compares candidate skills against job description required skills.
Calculates:
  - Matched Skills
  - Missing Skills
  - Extra Skills
  - Skill Score (out of 50)
"""
from typing import Dict, Any, List, Set

from ..constants import WEIGHTS


class SkillsEvaluator:
    """
    Evaluates skill match between resume and job description.

    Responsibility:
        Determine exact & case-insensitive match overlap between
        resume skills and job description required/preferred skills.
    """

    WEIGHT: int = WEIGHTS["skills"]

    def evaluate(
        self,
        resume_skills: List[str],
        jd_required_skills: List[str],
        jd_preferred_skills: List[str] = None,
    ) -> Dict[str, Any]:
        """
        Evaluate skill match.

        Args:
            resume_skills: List of candidate skills from ParsedResume.
            jd_required_skills: List of required skills from ParsedJobDescription.
            jd_preferred_skills: Optional list of preferred skills.

        Returns:
            Dict containing:
                - score: float (0 to 50)
                - max_score: 50
                - matched_skills: List[str]
                - missing_skills: List[str]
                - extra_skills: List[str]
                - match_percentage: float
        """
        max_score = self.WEIGHT
        jd_preferred_skills = jd_preferred_skills or []

        res_set: Set[str] = {s.lower().strip() for s in (resume_skills or []) if s}
        req_set: Set[str] = {s.lower().strip() for s in (jd_required_skills or []) if s}
        pref_set: Set[str] = {s.lower().strip() for s in (jd_preferred_skills or []) if s}

        # Original casing map for clean display output
        case_map: Dict[str, str] = {}
        for s in (resume_skills or []) + (jd_required_skills or []) + (jd_preferred_skills or []):
            if s:
                case_map[s.lower().strip()] = s.strip()

        # ── 1. Intersections ───────────────────────────────────────────────
        matched_keys = res_set & (req_set | pref_set)
        missing_keys = req_set - res_set
        extra_keys = res_set - (req_set | pref_set)

        matched_skills = [case_map.get(k, k.title()) for k in sorted(matched_keys)]
        missing_skills = [case_map.get(k, k.title()) for k in sorted(missing_keys)]
        extra_skills = [case_map.get(k, k.title()) for k in sorted(extra_keys)]

        # ── 2. Score Calculation ──────────────────────────────────────────
        total_req = len(req_set)
        if total_req == 0:
            # If JD specified no explicit skills, base score on candidate having skills
            score = max_score if len(res_set) >= 5 else (len(res_set) * 10)
            match_pct = 100.0
        else:
            matched_req_count = len(res_set & req_set)
            matched_pref_count = len(res_set & pref_set)

            # Base ratio from required skills
            ratio = matched_req_count / total_req
            base_score = ratio * max_score

            # Small bonus for preferred skills (max +5)
            pref_bonus = min(matched_pref_count * 2, 5)

            score = min(base_score + pref_bonus, max_score)
            match_pct = round((matched_req_count / total_req) * 100, 1)

        return {
            "score": round(score, 1),
            "max_score": max_score,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "extra_skills": extra_skills,
            "match_percentage": match_pct,
        }
