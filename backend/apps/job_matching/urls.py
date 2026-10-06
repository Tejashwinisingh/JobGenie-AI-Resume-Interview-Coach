"""
apps/job_matching/urls.py

URL routes for the Job Description Matching module.
"""
from django.urls import path

from .views import (
    JobDescriptionListCreateView,
    JobDescriptionDetailView,
    JobMatchView,
)

app_name = "job_matching"

urlpatterns = [
    path("", JobDescriptionListCreateView.as_view(), name="jd-list-create"),
    path("<int:pk>/", JobDescriptionDetailView.as_view(), name="jd-detail"),
    path("<int:pk>/match/<int:resume_id>/", JobMatchView.as_view(), name="jd-match"),
]
