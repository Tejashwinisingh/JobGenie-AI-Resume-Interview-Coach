"""
apps/ats/services.py

ATSService — Service layer for the ATS evaluation module.

Provides:
  - evaluate(resume): Run ATS engine, persist/update ATSScore, return instance.
  - get_or_evaluate(resume): Return existing score or trigger fresh evaluation.

This layer is the only entry point for the ATS evaluation; views and external
modules should call ATSService, never ATSEngine, directly.
"""
from typing import Optional

from .engine import ATSEngine
from .models import ATSScore


class ATSService:
    """
    Service layer that coordinates ATSEngine with database persistence.

    Usage:
        ats_score = ATSService.evaluate(resume)
        ats_score = ATSService.get_or_evaluate(resume)
    """

    @staticmethod
    def evaluate(resume) -> ATSScore:
        """
        Run a fresh ATS evaluation for the given resume and persist the result.

        This always overwrites any previously stored score for the resume.

        Args:
            resume: Resume model instance. Must have cleaned_text or raw_text.

        Returns:
            ATSScore model instance with the freshly computed result.

        Raises:
            ValueError: If the resume has no extractable text.
        """
        if not (resume.cleaned_text or resume.raw_text):
            raise ValueError(
                "Resume has no extracted text. Run text extraction (Module 3) first."
            )

        # Load parsed data if it exists
        parsed_resume: Optional[object] = None
        try:
            parsed_resume = resume.parsed_data  # type: ignore[attr-defined]
        except Exception:
            parsed_resume = None

        # Run the engine
        engine = ATSEngine()
        result = engine.run(resume, parsed_resume)

        # Upsert ATSScore record
        ats_score_obj, _ = ATSScore.objects.update_or_create(
            resume=resume,
            defaults={
                "ats_score":   result.ats_score,
                "grade":       result.grade,
                "grade_label": result.grade_label,
                "summary":     result.summary,
                "breakdown":   result.breakdown,
                "analysis":    result.analysis,
            },
        )
        return ats_score_obj

    @staticmethod
    def get_or_evaluate(resume) -> ATSScore:
        """
        Return the existing ATSScore for a resume, or evaluate if not yet scored.

        Args:
            resume: Resume model instance.

        Returns:
            ATSScore model instance.
        """
        try:
            return resume.ats_score  # type: ignore[attr-defined]
        except ATSScore.DoesNotExist:
            return ATSService.evaluate(resume)
