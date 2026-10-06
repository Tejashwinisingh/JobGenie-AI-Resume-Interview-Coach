"""
apps/interview_generator/urls.py

URL patterns for Module 8 — Interview Question Generator.
Included under the resumes namespace as:
  /api/resumes/<pk>/generate-questions/
  /api/resumes/<pk>/questions/
  /api/resumes/<pk>/questions/<qs_id>/
"""
from django.urls import path

from .views import (
    GenerateQuestionsView,
    QuestionSetDetailView,
    QuestionSetListView,
)

urlpatterns = [
    path("", GenerateQuestionsView.as_view(), name="generate-questions"),
    path("list/", QuestionSetListView.as_view(), name="question-set-list"),
    path("<int:qs_id>/", QuestionSetDetailView.as_view(), name="question-set-detail"),
]
