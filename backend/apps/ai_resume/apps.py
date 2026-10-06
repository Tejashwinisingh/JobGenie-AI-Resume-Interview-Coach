"""
apps/ai_resume/apps.py
Django AppConfig for the AI Resume Improvement Suggestions module.
"""
from django.apps import AppConfig


class AiResumeConfig(AppConfig):
    """Configuration for the AI Resume app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.ai_resume"
    verbose_name = "AI Resume Improvement Suggestions"
