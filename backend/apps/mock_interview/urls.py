"""
apps/mock_interview/urls.py

URL patterns for Module 9 — AI Mock Interview System.
Included in root urls.py under /api/interviews/
"""
from django.urls import path

from .views import (
    FinishInterviewView,
    InterviewSessionDetailView,
    InterviewSessionListView,
    StartInterviewView,
    SubmitAnswerView,
)

app_name = "mock_interview"

urlpatterns = [
    path("", InterviewSessionListView.as_view(), name="session-list"),
    path("start/", StartInterviewView.as_view(), name="session-start"),
    path("<int:session_id>/", InterviewSessionDetailView.as_view(), name="session-detail"),
    path("<int:session_id>/answer/", SubmitAnswerView.as_view(), name="session-answer"),
    path("<int:session_id>/finish/", FinishInterviewView.as_view(), name="session-finish"),
]
