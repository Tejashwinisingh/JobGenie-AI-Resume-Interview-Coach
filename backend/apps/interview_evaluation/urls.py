"""
apps/interview_evaluation/urls.py

URL routing for Module 10 — AI Answer Evaluation & Interview Analysis Engine.
Included in root urls.py under /api/interviews/
"""
from django.urls import path

from .views import (
    EvaluateInterviewSessionView,
    RetrieveInterviewEvaluationView,
)

app_name = "interview_evaluation"

urlpatterns = [
    path("<int:session_id>/evaluate/", EvaluateInterviewSessionView.as_view(), name="session-evaluate"),
    path("<int:session_id>/evaluation/", RetrieveInterviewEvaluationView.as_view(), name="session-evaluation-detail"),
]
