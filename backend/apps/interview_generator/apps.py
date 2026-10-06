"""
apps/interview_generator/apps.py
"""
from django.apps import AppConfig


class InterviewGeneratorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.interview_generator'
    verbose_name = 'Interview Question Generator'
