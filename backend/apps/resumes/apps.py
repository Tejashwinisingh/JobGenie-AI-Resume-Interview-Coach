"""
apps/resumes/apps.py
AppConfig for the resumes module.
"""
from django.apps import AppConfig


class ResumesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.resumes'
    verbose_name = 'Resumes'
