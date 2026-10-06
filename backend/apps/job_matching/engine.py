"""
apps/job_matching/engine.py

JobMatchingEngine — Orchestrator for comparing parsed resumes with Job Descriptions.

Runs all 5 evaluators (Skills, Experience, Education, Certifications, Keywords)
and returns a structured MatchResult.
"""
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

from .scoring import JobMatchingScorer
from .evaluators.skills import SkillsEvaluator
from .evaluators.experience import ExperienceEvaluator
from .evaluators.education import EducationEvaluator
from .evaluators.certifications import CertificationsEvaluator
from .evaluators.keywords import KeywordsEvaluator


@dataclass
class MatchResult:
    """
    Immutable result object returned by JobMatchingEngine.run().
    """
    match_score: int
    grade: str
    grade_label: str
    matched_skills: List[str] = field(default_factory=list)
    missing_skills: List[str] = field(default_factory=list)
    extra_skills: List[str] = field(default_factory=list)
    skill_match_score: int = 0
    experience_score: int = 0
    education_score: int = 0
    certification_score: int = 0
    keyword_score: int = 0
    breakdown: Dict[str, Any] = field(default_factory=dict)


class JobMatchingEngine:
    """
    Orchestrates job matching evaluation pipeline.

    Usage:
        engine = JobMatchingEngine()
        result = engine.run(resume, parsed_resume, job_description)
    """

    def __init__(
        self,
        skills_evaluator: Optional[SkillsEvaluator] = None,
        experience_evaluator: Optional[ExperienceEvaluator] = None,
        education_evaluator: Optional[EducationEvaluator] = None,
        certifications_evaluator: Optional[CertificationsEvaluator] = None,
        keywords_evaluator: Optional[KeywordsEvaluator] = None,
    ) -> None:
        self._skills = skills_evaluator or SkillsEvaluator()
        self._experience = experience_evaluator or ExperienceEvaluator()
        self._education = education_evaluator or EducationEvaluator()
        self._certifications = certifications_evaluator or CertificationsEvaluator()
        self._keywords = keywords_evaluator or KeywordsEvaluator()

    def run(
        self,
        resume: Any,
        parsed_resume: Any,
        job_description: Any,
    ) -> MatchResult:
        """
        Execute job description matching against a candidate's resume.

        Args:
            resume: Resume model instance (cleaned_text, raw_text).
            parsed_resume: ParsedResume model instance (skills, education, etc.).
            job_description: JobDescription model instance (cleaned_text, parsed_data).

        Returns:
            MatchResult dataclass.
        """
        jd_parsed = getattr(job_description, "parsed_data", {}) or {}
        req_skills = jd_parsed.get("required_skills", [])
        pref_skills = jd_parsed.get("preferred_skills", [])
        req_years = float(jd_parsed.get("experience_years", 0.0))
        req_degree = jd_parsed.get("required_degree", "")
        req_certs = jd_parsed.get("certifications", [])

        # Extract candidate data safely
        res_skills = getattr(parsed_resume, "skills", []) if parsed_resume else []
        res_edu = getattr(parsed_resume, "education", []) if parsed_resume else []
        res_exp = getattr(parsed_resume, "experience", []) if parsed_resume else []
        res_certs = getattr(parsed_resume, "certifications", []) if parsed_resume else []

        resume_text = (getattr(resume, "cleaned_text", "") or getattr(resume, "raw_text", "")) if resume else ""
        if not isinstance(resume_text, str):
            resume_text = str(resume_text or "")

        jd_text = (getattr(job_description, "cleaned_text", "") or getattr(job_description, "description", "")) if job_description else ""
        if not isinstance(jd_text, str):
            jd_text = str(jd_text or "")

        # ── 1. Execute Evaluators ──────────────────────────────────────────
        sk_result = self._skills.evaluate(res_skills, req_skills, pref_skills)
        exp_result = self._experience.evaluate(res_exp, req_years)
        edu_result = self._education.evaluate(res_edu, req_degree)
        cert_result = self._certifications.evaluate(res_certs, req_certs)
        kw_result = self._keywords.evaluate(resume_text, jd_text)

        # ── 2. Breakdown ──────────────────────────────────────────────────
        breakdown_scores = {
            "skills": float(sk_result["score"]),
            "experience": float(exp_result["score"]),
            "education": float(edu_result["score"]),
            "certifications": float(cert_result["score"]),
            "keywords": float(kw_result["score"]),
        }

        total_score = JobMatchingScorer.compute_total(breakdown_scores)
        grade, grade_label = JobMatchingScorer.compute_grade(total_score)

        return MatchResult(
            match_score=total_score,
            grade=grade_label,  # Grade label output as requested in spec e.g. "Very Good"
            grade_label=grade_label,
            matched_skills=sk_result["matched_skills"],
            missing_skills=sk_result["missing_skills"],
            extra_skills=sk_result["extra_skills"],
            skill_match_score=int(round(sk_result["score"])),
            experience_score=int(round(exp_result["score"])),
            education_score=int(round(edu_result["score"])),
            certification_score=int(round(cert_result["score"])),
            keyword_score=int(round(kw_result["score"])),
            breakdown=breakdown_scores,
        )
