"""
apps/mock_interview/apps.py
"""
from django.apps import AppConfig


class MockInterviewConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.mock_interview'
    verbose_name = 'AI Mock Interview System'
