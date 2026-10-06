"""
apps/mock_interview/models.py

Models for Module 9 — AI Mock Interview System.
Designed to be fully compatible with Module 10 (AI Answer Evaluation Engine)
without requiring any structural modifications.
"""
from django.conf import settings
from django.db import models

from .constants import (
    DIFFICULTY_CHOICES,
    DIFFICULTY_MEDIUM,
    INTERVIEW_TYPE_CHOICES,
    STATUS_CHOICES,
    STATUS_IN_PROGRESS,
    TYPE_MIXED,
)


class InterviewSession(models.Model):
    """
    Stores a complete mock interview session.

    Tracks session status, current progress, candidate profile, and metadata.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="mock_interviews",
        help_text="The candidate taking this interview.",
    )
    resume = models.ForeignKey(
        "resumes.Resume",
        on_delete=models.CASCADE,
        related_name="mock_interviews",
        help_text="The resume used for this interview.",
    )
    job_description = models.ForeignKey(
        "job_matching.JobDescription",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="mock_interviews",
        help_text="Optional target job description.",
    )
    role = models.CharField(
        max_length=200,
        default="Software Engineer",
        help_text="Target job role (e.g., Python Developer, Backend Engineer).",
    )
    difficulty = models.CharField(
        max_length=20,
        choices=DIFFICULTY_CHOICES,
        default=DIFFICULTY_MEDIUM,
        help_text="Difficulty level: Easy | Medium | Hard",
    )
    interview_type = models.CharField(
        max_length=50,
        choices=INTERVIEW_TYPE_CHOICES,
        default=TYPE_MIXED,
        help_text="Type of interview: HR | Technical | Behavioral | Coding | Project Discussion | Mixed",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_IN_PROGRESS,
        db_index=True,
        help_text="Session status: in_progress | completed | abandoned",
    )
    current_question = models.PositiveIntegerField(
        default=1,
        help_text="1-based index of the active question.",
    )
    total_questions = models.PositiveIntegerField(
        default=10,
        help_text="Total number of questions in this interview.",
    )
    completed_questions = models.PositiveIntegerField(
        default=0,
        help_text="Number of questions answered by the candidate.",
    )
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = "mock_interview"
        verbose_name = "Interview Session"
        verbose_name_plural = "Interview Sessions"
        ordering = ["-started_at"]

    def __str__(self) -> str:
        return f"Mock Interview #{self.pk} | {self.role} ({self.difficulty}) | Status: {self.status}"

    @property
    def remaining_questions(self) -> int:
        """Calculate remaining unanswered questions."""
        return max(0, self.total_questions - self.completed_questions)

    @property
    def progress(self) -> int:
        """Calculate completion percentage (0-100)."""
        if self.total_questions <= 0:
            return 0
        return min(100, int((self.completed_questions / self.total_questions) * 100))


class InterviewQuestion(models.Model):
    """
    Stores an individual question asked during a mock interview session along with
    the candidate's submitted answer.

    Designed for Module 10 to evaluate every question/answer pair seamlessly.
    """

    session = models.ForeignKey(
        InterviewSession,
        on_delete=models.CASCADE,
        related_name="questions",
        help_text="The parent interview session.",
    )
    question_number = models.PositiveIntegerField(
        help_text="Sequence index of the question within the session (1..N).",
    )
    category = models.CharField(
        max_length=50,
        default="Technical",
        help_text="Question category: HR | Technical | Resume | Project | Coding | Behavioral",
    )
    question = models.TextField(
        help_text="The interview question text presented to the candidate.",
    )
    user_answer = models.TextField(
        blank=True,
        default="",
        help_text="The candidate's response text.",
    )
    answered_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when the candidate submitted their answer.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "mock_interview"
        verbose_name = "Interview Question"
        verbose_name_plural = "Interview Questions"
        ordering = ["session", "question_number"]
        unique_together = [("session", "question_number")]

    def __str__(self) -> str:
        return f"Session #{self.session_id} - Q{self.question_number} [{self.category}]: {self.question[:50]}"
