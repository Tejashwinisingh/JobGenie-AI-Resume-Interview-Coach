"""
apps/interview_evaluation/apps.py
"""
from django.apps import AppConfig


class InterviewEvaluationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.interview_evaluation'
    verbose_name = 'AI Answer Evaluation Engine'
