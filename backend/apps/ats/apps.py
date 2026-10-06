"""
apps/ats/apps.py
Django AppConfig for the ATS (Applicant Tracking System) module.
"""
from django.apps import AppConfig


class AtsConfig(AppConfig):
    """Configuration for the ATS analysis app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.ats"
    verbose_name = "ATS Analysis"
