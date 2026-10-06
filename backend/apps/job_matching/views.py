"""
apps/job_matching/views.py

API Views for the Job Description Matching module:
  POST /api/job-descriptions/                    → JobDescriptionListCreateView (create/upload JD)
  GET  /api/job-descriptions/                    → JobDescriptionListCreateView (list user's JDs)
  GET  /api/job-descriptions/<id>/               → JobDescriptionDetailView (retrieve JD details)
  POST /api/job-descriptions/<id>/match/<resume_id>/ → JobMatchView (generate match report)
  GET  /api/job-descriptions/<id>/match/<resume_id>/ → JobMatchView (retrieve match report)
"""
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.resumes.models import Resume
from .models import JobDescription, JobMatch
from .serializers import (
    JobDescriptionSerializer,
    JobDescriptionCreateSerializer,
    JobMatchSerializer,
)
from .services import JobMatchingService


def _get_user_jd(pk: int, user) -> JobDescription | None:
    """Return JobDescription if exists and belongs to user."""
    try:
        return JobDescription.objects.get(pk=pk, user=user)
    except JobDescription.DoesNotExist:
        return None


def _get_user_resume(pk: int, user) -> Resume | None:
    """Return Resume if exists and belongs to user."""
    try:
        return Resume.objects.get(pk=pk, user=user)
    except Resume.DoesNotExist:
        return None


class JobDescriptionListCreateView(APIView):
    """
    POST /api/job-descriptions/ — Create or Upload a Job Description.
    GET  /api/job-descriptions/ — List all Job Descriptions for authenticated user.
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request) -> Response:
        jds = JobDescription.objects.filter(user=request.user)
        serializer = JobDescriptionSerializer(jds, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request) -> Response:
        create_serializer = JobDescriptionCreateSerializer(data=request.data)
        if not create_serializer.is_valid():
            return Response(create_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        title = create_serializer.validated_data.get("title", "")
        company = create_serializer.validated_data.get("company", "")
        description = create_serializer.validated_data.get("description", "")
        file_obj = create_serializer.validated_data.get("file")

        try:
            jd = JobMatchingService.create_job_description(
                user=request.user,
                title=title,
                company=company,
                description=description,
                file_obj=file_obj,
            )
            response_serializer = JobDescriptionSerializer(jd)
            return Response(
                {
                    "message": "Job Description created and parsed successfully.",
                    "data": response_serializer.data,
                },
                status=status.HTTP_201_CREATED,
            )
        except Exception as exc:
            return Response(
                {"detail": f"Failed to process Job Description: {str(exc)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class JobDescriptionDetailView(APIView):
    """
    GET /api/job-descriptions/<id>/ — Retrieve details for a specific Job Description.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk: int) -> Response:
        jd = _get_user_jd(pk, request.user)
        if not jd:
            return Response(
                {"detail": "Job Description not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = JobDescriptionSerializer(jd)
        return Response(serializer.data, status=status.HTTP_200_OK)


class JobMatchView(APIView):
    """
    POST /api/job-descriptions/<id>/match/<resume_id>/ — Generate match report.
    GET  /api/job-descriptions/<id>/match/<resume_id>/ — Retrieve match report.
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser]

    def post(self, request, pk: int, resume_id: int) -> Response:
        jd = _get_user_jd(pk, request.user)
        if not jd:
            return Response(
                {"detail": "Job Description not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        resume = _get_user_resume(resume_id, request.user)
        if not resume:
            return Response(
                {"detail": "Resume not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not jd.cleaned_text and not jd.description:
            return Response(
                {"detail": "Job Description content is empty."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            job_match = JobMatchingService.match_resume_to_jd(jd, resume)
            serializer = JobMatchSerializer(job_match)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as exc:
            return Response(
                {"detail": f"Matching failed: {str(exc)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def get(self, request, pk: int, resume_id: int) -> Response:
        jd = _get_user_jd(pk, request.user)
        if not jd:
            return Response(
                {"detail": "Job Description not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        resume = _get_user_resume(resume_id, request.user)
        if not resume:
            return Response(
                {"detail": "Resume not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            job_match = JobMatch.objects.get(job_description=jd, resume=resume)
            serializer = JobMatchSerializer(job_match)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except JobMatch.DoesNotExist:
            # If not yet generated, trigger calculation
            try:
                job_match = JobMatchingService.match_resume_to_jd(jd, resume)
                serializer = JobMatchSerializer(job_match)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except Exception as exc:
                return Response(
                    {"detail": f"Match report not found and calculation failed: {str(exc)}"},
                    status=status.HTTP_404_NOT_FOUND,
                )
