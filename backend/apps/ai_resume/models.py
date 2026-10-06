"""
apps/ai_resume/models.py

ResumeSuggestion model — stores AI improvement feedback for a resume.
"""
from django.db import models


class ResumeSuggestion(models.Model):
    """
    Stores AI-generated feedback and suggestions for a candidate resume.
    """

    resume = models.OneToOneField(
        "resumes.Resume",
        on_delete=models.CASCADE,
        related_name="ai_suggestions",
    )
    summary = models.TextField(help_text="Overall assessment summary.")
    strengths = models.JSONField(default=list, blank=True, help_text="List of resume strengths.")
    weaknesses = models.JSONField(default=list, blank=True, help_text="List of areas needing improvement.")
    suggestions = models.JSONField(default=list, blank=True, help_text="List of actionable suggestions.")
    priority_skills = models.JSONField(default=list, blank=True, help_text="Priority learning roadmap skills.")
    improved_project_description = models.TextField(blank=True, default="", help_text="Sample rewritten project description.")
    created_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "ai_resume"
        verbose_name = "AI Resume Suggestion"
        verbose_name_plural = "AI Resume Suggestions"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"AI Suggestions for Resume #{self.resume_id}"
