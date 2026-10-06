"""
apps/ats/engine.py

ATSEngine — Orchestrator for the ATS evaluation pipeline.

Runs all evaluators, aggregates results into a structured ATSResult,
and is designed to be reusable by future modules (Job Description Matching,
Skill Gap Analysis, OpenAI Suggestions) without modification.
"""
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, TYPE_CHECKING

from .scoring import ATSScorer
from .evaluators.formatting import FormattingEvaluator
from .evaluators.contact import ContactEvaluator
from .evaluators.structure import StructureEvaluator
from .evaluators.keywords import KeywordsEvaluator
from .evaluators.skills import SkillsEvaluator
from .evaluators.education import EducationEvaluator
from .evaluators.experience import ExperienceEvaluator
from .evaluators.projects import ProjectsEvaluator


# ─── Result Dataclass ─────────────────────────────────────────────────────────

@dataclass
class ATSResult:
    """
    Immutable value object returned by ATSEngine.run().

    Attributes:
        ats_score:             Final integer score (0–100).
        grade:                 Letter grade (A+, A, B, C, D).
        grade_label:           Human label (Excellent, Very Good, …).
        summary:               One-paragraph human-readable assessment.
        breakdown:             Per-category scores dict.
        analysis:              Detailed findings dict (keywords, warnings, missing).
    """
    ats_score: int
    grade: str
    grade_label: str
    summary: str
    breakdown: Dict[str, int] = field(default_factory=dict)
    analysis: Dict[str, Any] = field(default_factory=dict)


# ─── Engine ───────────────────────────────────────────────────────────────────

class ATSEngine:
    """
    Orchestrates all ATS evaluators and produces an ATSResult.

    Evaluators are injected at construction time to allow:
      - Unit testing with mock evaluators
      - Future extension (e.g. inject JD-matching evaluator)
      - Easy swap of scoring weights without changing call sites

    Usage:
        engine = ATSEngine()
        result = engine.run(resume, parsed_resume)
    """

    def __init__(
        self,
        formatting_evaluator: Optional[FormattingEvaluator] = None,
        contact_evaluator: Optional[ContactEvaluator] = None,
        structure_evaluator: Optional[StructureEvaluator] = None,
        keywords_evaluator: Optional[KeywordsEvaluator] = None,
        skills_evaluator: Optional[SkillsEvaluator] = None,
        education_evaluator: Optional[EducationEvaluator] = None,
        experience_evaluator: Optional[ExperienceEvaluator] = None,
        projects_evaluator: Optional[ProjectsEvaluator] = None,
        scorer: Optional[ATSScorer] = None,
    ) -> None:
        self._formatting  = formatting_evaluator  or FormattingEvaluator()
        self._contact     = contact_evaluator     or ContactEvaluator()
        self._structure   = structure_evaluator   or StructureEvaluator()
        self._keywords    = keywords_evaluator    or KeywordsEvaluator()
        self._skills      = skills_evaluator      or SkillsEvaluator()
        self._education   = education_evaluator   or EducationEvaluator()
        self._experience  = experience_evaluator  or ExperienceEvaluator()
        self._projects    = projects_evaluator    or ProjectsEvaluator()
        self._scorer      = scorer                or ATSScorer()

    def run(self, resume: Any, parsed_resume: Optional[Any]) -> ATSResult:
        """
        Execute the full ATS evaluation pipeline.

        Args:
            resume:        Resume model instance (has cleaned_text, raw_text, file_type).
            parsed_resume: ParsedResume model instance (has skills, education, etc.)
                           or None if not yet parsed.

        Returns:
            ATSResult dataclass with full score, breakdown, and analysis.
        """
        cleaned_text: str = resume.cleaned_text or ""
        raw_text: str = resume.raw_text or ""

        # Build parsed_data dict (safe even if parsed_resume is None)
        if parsed_resume is not None:
            parsed_data = {
                "name":         getattr(parsed_resume, "name", ""),
                "email":        getattr(parsed_resume, "email", ""),
                "phone":        getattr(parsed_resume, "phone", ""),
                "linkedin":     getattr(parsed_resume, "linkedin", ""),
                "github":       getattr(parsed_resume, "github", ""),
                "skills":       getattr(parsed_resume, "skills", []) or [],
                "education":    getattr(parsed_resume, "education", []) or [],
                "experience":   getattr(parsed_resume, "experience", []) or [],
                "projects":     getattr(parsed_resume, "projects", []) or [],
                "certifications": getattr(parsed_resume, "certifications", []) or [],
            }
        else:
            parsed_data = {
                "name": "", "email": "", "phone": "",
                "linkedin": "", "github": "",
                "skills": [], "education": [], "experience": [],
                "projects": [], "certifications": [],
            }

        # ── Run all evaluators ─────────────────────────────────────────────
        fmt_result  = self._formatting.evaluate(cleaned_text, raw_text)
        cont_result = self._contact.evaluate(parsed_data)
        struct_result = self._structure.evaluate(cleaned_text)
        kw_result   = self._keywords.evaluate(cleaned_text)
        sk_result   = self._skills.evaluate(parsed_data.get("skills", []))
        edu_result  = self._education.evaluate(parsed_data.get("education", []))
        exp_result  = self._experience.evaluate(parsed_data.get("experience", []))
        proj_result = self._projects.evaluate(parsed_data.get("projects", []))

        # ── Build breakdown ────────────────────────────────────────────────
        breakdown: Dict[str, int] = {
            "formatting": fmt_result["score"],
            "contact":    cont_result["score"],
            "structure":  struct_result["score"],
            "keywords":   kw_result["score"],
            "skills":     sk_result["score"],
            "education":  edu_result["score"],
            "experience": exp_result["score"],
            "projects":   proj_result["score"],
        }

        total_score = ATSScorer.compute_total(breakdown)
        grade, grade_label = ATSScorer.compute_grade(total_score)
        summary = ATSScorer.compute_summary(total_score, grade, grade_label)

        # ── Aggregate all warnings ─────────────────────────────────────────
        all_warnings: List[str] = []
        for result in [fmt_result, cont_result, struct_result, kw_result,
                       sk_result, edu_result, exp_result, proj_result]:
            all_warnings.extend(result.get("warnings", []))

        # Deduplicate while preserving order
        seen_warnings: set = set()
        unique_warnings: List[str] = []
        for w in all_warnings:
            if w not in seen_warnings:
                seen_warnings.add(w)
                unique_warnings.append(w)

        # ── Build analysis dict ────────────────────────────────────────────
        analysis: Dict[str, Any] = {
            "technical_keywords_found": kw_result.get("keywords_found", []),
            "keyword_count": kw_result.get("keyword_count", 0),
            "missing_sections": struct_result.get("missing_sections", []),
            "found_sections": struct_result.get("found_sections", []),
            "warnings": unique_warnings,
            "contact_details": cont_result.get("details", {}),
            "formatting_details": fmt_result.get("details", {}),
            "skills_details": sk_result.get("details", {}),
            "education_details": edu_result.get("details", {}),
            "experience_details": exp_result.get("details", {}),
            "projects_details": proj_result.get("details", {}),
        }

        return ATSResult(
            ats_score=total_score,
            grade=grade,
            grade_label=grade_label,
            summary=summary,
            breakdown=breakdown,
            analysis=analysis,
        )
