"""
apps/ai_resume/urls.py

URL routes for the AI Resume Improvement Suggestions module.
Included under resumes namespace:
  POST /api/resumes/<id>/ai-suggestions/
  GET  /api/resumes/<id>/ai-suggestions/
"""
from django.urls import path

from .views import AISuggestionView

urlpatterns = [
    path("", AISuggestionView.as_view(), name="ai-suggestions"),
]
