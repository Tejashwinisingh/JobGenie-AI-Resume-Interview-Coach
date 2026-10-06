"""
apps/resumes/urls.py
URL routes for the resumes module — Modules 2, 3, 4, 5, 7, 8.
"""
from django.urls import path, include

from .views import (
    ResumeListCreateView,
    ResumeDetailView,
    ResumeProcessView,
    ResumeTextView,
    ResumeParseView,
    ResumeParsedDataView,
)

app_name = 'resumes'

urlpatterns = [
    path('', ResumeListCreateView.as_view(), name='resume-list-create'),
    path('<int:pk>/', ResumeDetailView.as_view(), name='resume-detail'),
    path('<int:pk>/process/', ResumeProcessView.as_view(), name='resume-process'),
    path('<int:pk>/text/', ResumeTextView.as_view(), name='resume-text'),
    path('<int:pk>/parse/', ResumeParseView.as_view(), name='resume-parse'),
    path('<int:pk>/parsed/', ResumeParsedDataView.as_view(), name='resume-parsed'),
    # Module 5 – ATS Quality Score
    path('<int:pk>/ats-score/', include('apps.ats.urls')),
    # Module 7 – AI Resume Improvement Suggestions
    path('<int:pk>/ai-suggestions/', include('apps.ai_resume.urls')),
    # Module 8 – Interview Question Generator
    path('<int:pk>/generate-questions/', include('apps.interview_generator.urls')),
    path('<int:pk>/questions/', include('apps.interview_generator.urls')),
]
