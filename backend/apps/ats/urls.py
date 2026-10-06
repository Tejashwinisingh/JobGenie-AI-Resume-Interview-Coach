"""
apps/ats/urls.py

URL routes for the ATS module.
These are included under the resumes namespace:
  POST /api/resumes/<id>/ats-score/
  GET  /api/resumes/<id>/ats-score/
"""
from django.urls import path

from .views import ATSScoreView

urlpatterns = [
    path("", ATSScoreView.as_view(), name="ats-score"),
]
