"""
apps/job_matching/apps.py
Django AppConfig for the Job Description Matching module.
"""
from django.apps import AppConfig


class JobMatchingConfig(AppConfig):
    """Configuration for the Job Matching app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.job_matching"
    verbose_name = "Job Description Matching"
