"""
core/urls.py
Root URL configuration.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.authentication.urls', namespace='authentication')),
    path('api/resumes/', include('apps.resumes.urls', namespace='resumes')),
    path('api/job-descriptions/', include('apps.job_matching.urls', namespace='job_matching')),
    path('api/interviews/', include('apps.mock_interview.urls', namespace='mock_interview')),
    path('api/interviews/', include('apps.interview_evaluation.urls', namespace='interview_evaluation')),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
