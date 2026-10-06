"""
apps/interview_generator/models.py

InterviewQuestionSet — stores AI-generated interview questions for a resume.
"""
from django.db import models

from .constants import DIFFICULTY_CHOICES, DIFFICULTY_MEDIUM


class InterviewQuestionSet(models.Model):
    """
    Stores a set of AI-generated interview questions for a candidate resume.

    Designed to support future modules:
    - AI Mock Interview (answer submission and evaluation)
    - AI Answer Evaluator (score per question)
    """

    resume = models.ForeignKey(
        "resumes.Resume",
        on_delete=models.CASCADE,
        related_name="interview_question_sets",
        help_text="The resume this question set was generated for.",
    )
    job_role = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="Target job role (e.g. Backend Developer).",
    )
    difficulty = models.CharField(
        max_length=20,
        choices=DIFFICULTY_CHOICES,
        default=DIFFICULTY_MEDIUM,
        help_text="Interview difficulty level.",
    )
    question_count = models.PositiveSmallIntegerField(
        default=10,
        help_text="Number of questions generated.",
    )
    questions = models.JSONField(
        default=list,
        help_text="List of {id, category, question} dicts.",
    )
    provider = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text="AI provider used (OpenRouter / OpenAI / Fallback).",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "interview_generator"
        verbose_name = "Interview Question Set"
        verbose_name_plural = "Interview Question Sets"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return (
            f"Interview Q-Set #{self.pk} | Resume #{self.resume_id} | "
            f"{self.difficulty} | {self.job_role} | {self.question_count}Q"
        )
