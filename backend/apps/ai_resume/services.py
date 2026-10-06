"""
apps/ai_resume/services.py

AISuggestionService — Service layer coordinating context assembly, OpenAI client calls, and database persistence.
"""
from typing import Optional

from apps.resumes.services import ResumeTextExtractorService
from apps.ats.services import ATSService
from .models import ResumeSuggestion
from .openai_client import OpenAIResumeClient
from .utils import build_resume_ai_context


class AISuggestionService:
    """
    Service layer for AI Resume Suggestions.
    """

    @classmethod
    def generate_suggestions(cls, resume, client: Optional[OpenAIResumeClient] = None) -> ResumeSuggestion:
        """
        Generate AI suggestions for a candidate resume and persist in database.

        Args:
            resume: Resume model instance.
            client: Optional OpenAIResumeClient (injectable for testing).

        Returns:
            ResumeSuggestion instance.
        """
        # Ensure resume has extracted text and parsed data
        if not (resume.cleaned_text or resume.raw_text):
            ResumeTextExtractorService.process_resume(resume)
            resume.refresh_from_db()

        if not hasattr(resume, "parsed_data") or resume.parsed_data is None:
            ResumeTextExtractorService.parse_and_store_resume(resume)
            resume.refresh_from_db()

        parsed_resume = getattr(resume, "parsed_data", None)

        # Ensure ATS score exists
        ats_score_obj = ATSService.get_or_evaluate(resume)

        # Get latest job match report if available
        job_match_obj = None
        if hasattr(resume, "job_matches") and resume.job_matches.exists():
            job_match_obj = resume.job_matches.first()

        # Build context payload
        context = build_resume_ai_context(
            resume=resume,
            parsed_resume=parsed_resume,
            ats_score_obj=ats_score_obj,
            job_match_obj=job_match_obj,
        )

        # Call OpenAI client
        ai_client = client or OpenAIResumeClient()
        ai_output = ai_client.generate_suggestions(context)

        # Persist in database
        suggestion_obj, _ = ResumeSuggestion.objects.update_or_create(
            resume=resume,
            defaults={
                "summary": ai_output.get("summary", ""),
                "strengths": ai_output.get("strengths", []),
                "weaknesses": ai_output.get("weaknesses", []),
                "suggestions": ai_output.get("suggestions", []),
                "priority_skills": ai_output.get("priority_skills", []),
                "improved_project_description": ai_output.get("improved_project_description", ""),
            },
        )
        return suggestion_obj

    @classmethod
    def get_or_generate_suggestions(cls, resume) -> ResumeSuggestion:
        """
        Retrieve existing AI suggestions for resume, or generate fresh ones.
        """
        try:
            return resume.ai_suggestions
        except ResumeSuggestion.DoesNotExist:
            return cls.generate_suggestions(resume)
