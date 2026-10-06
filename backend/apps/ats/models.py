"""
apps/ats/models.py

ATSScore model — stores the ATS evaluation result for a resume.
One resume has at most one ATS score record (OneToOneField).
"""
from django.db import models


class ATSScore(models.Model):
    """
    Stores the ATS analysis result for a single resume.

    Fields:
        resume       – The parent resume (cascades on delete).
        ats_score    – Integer score 0–100.
        grade        – Letter grade (A+, A, B, C, D).
        grade_label  – Human label (Excellent, Very Good, …).
        summary      – One-sentence assessment string.
        breakdown    – JSON dict of per-category scores.
        analysis     – JSON dict with keywords, warnings, missing sections.
        evaluated_at – Timestamp of the last evaluation (auto-updated).
    """

    resume = models.OneToOneField(
        "resumes.Resume",
        on_delete=models.CASCADE,
        related_name="ats_score",
    )
    ats_score = models.PositiveSmallIntegerField(
        help_text="ATS score out of 100."
    )
    grade = models.CharField(
        max_length=5,
        help_text="Letter grade: A+, A, B, C, D.",
    )
    grade_label = models.CharField(
        max_length=30,
        default="",
        help_text="Human-readable grade label.",
    )
    summary = models.TextField(
        blank=True,
        default="",
        help_text="Human-readable assessment summary.",
    )
    breakdown = models.JSONField(
        default=dict,
        help_text="Per-category score breakdown.",
    )
    analysis = models.JSONField(
        default=dict,
        help_text="Full analysis: keywords found, warnings, missing sections.",
    )
    evaluated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "ats"
        verbose_name = "ATS Score"
        verbose_name_plural = "ATS Scores"
        ordering = ["-evaluated_at"]

    def __str__(self) -> str:
        return (
            f"ATS Score for Resume #{self.resume_id} — "
            f"{self.ats_score}/100 ({self.grade})"
        )
