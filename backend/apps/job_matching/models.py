"""
apps/job_matching/models.py

Models for the Job Description Matching module:
  - JobDescription: Stores uploaded or pasted job descriptions and parsed requirements.
  - JobMatch: Stores the output of matching a specific resume against a Job Description.
"""
import os
from django.db import models
from django.conf import settings


def jd_upload_path(instance, filename: str) -> str:
    """Store job description files in a per-user subdirectory: job_descriptions/<user_id>/<filename>."""
    return os.path.join("job_descriptions", str(instance.user.id), filename)


class JobDescription(models.Model):
    """
    Stores a Job Description (pasted text or uploaded PDF/DOCX file).
    """

    FILE_TYPE_TEXT = "text"
    FILE_TYPE_PDF = "pdf"
    FILE_TYPE_DOCX = "docx"
    FILE_TYPE_CHOICES = [
        (FILE_TYPE_TEXT, "Text"),
        (FILE_TYPE_PDF, "PDF"),
        (FILE_TYPE_DOCX, "DOCX"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="job_descriptions",
    )
    title = models.CharField(max_length=255, help_text="Job title or role name.")
    company = models.CharField(max_length=255, blank=True, default="", help_text="Company or organization name.")
    description = models.TextField(blank=True, default="", help_text="Raw or pasted job description text.")
    file = models.FileField(upload_to=jd_upload_path, blank=True, null=True)
    file_type = models.CharField(max_length=10, choices=FILE_TYPE_CHOICES, default=FILE_TYPE_TEXT)

    raw_text = models.TextField(blank=True, null=True)
    cleaned_text = models.TextField(blank=True, null=True)
    parsed_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Structured requirements (required_skills, preferred_skills, experience_years, required_degree, etc.)",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "job_matching"
        ordering = ["-created_at"]
        verbose_name = "Job Description"
        verbose_name_plural = "Job Descriptions"

    def __str__(self) -> str:
        return f"{self.title} ({self.company or 'General'}) — #{self.id}"

    def delete(self, *args, **kwargs):
        """Remove physical file from disk on deletion if present."""
        if self.file:
            storage = self.file.storage
            path = self.file.name
            super().delete(*args, **kwargs)
            if path and storage.exists(path):
                storage.delete(path)
        else:
            super().delete(*args, **kwargs)


class JobMatch(models.Model):
    """
    Stores the match report between a JobDescription and a Resume.
    """

    job_description = models.ForeignKey(
        JobDescription,
        on_delete=models.CASCADE,
        related_name="matches",
    )
    resume = models.ForeignKey(
        "resumes.Resume",
        on_delete=models.CASCADE,
        related_name="job_matches",
    )

    match_score = models.PositiveSmallIntegerField(help_text="Total match score (0-100).")
    grade = models.CharField(max_length=50, help_text="Match grade label (e.g. Excellent Match, Very Good, Good Match).")

    matched_skills = models.JSONField(default=list, blank=True)
    missing_skills = models.JSONField(default=list, blank=True)
    extra_skills = models.JSONField(default=list, blank=True)

    experience_score = models.PositiveSmallIntegerField(default=0)
    education_score = models.PositiveSmallIntegerField(default=0)
    certification_score = models.PositiveSmallIntegerField(default=0)
    keyword_score = models.PositiveSmallIntegerField(default=0)

    breakdown = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "job_matching"
        ordering = ["-created_at"]
        verbose_name = "Job Match"
        verbose_name_plural = "Job Matches"
        unique_together = ("job_description", "resume")

    def __str__(self) -> str:
        return f"Match #{self.id}: Resume #{self.resume_id} vs JD #{self.job_description_id} ({self.match_score}%)"
