"""
apps/interview_generator/views.py

API Views for the Interview Question Generator — Module 8:
  POST /api/resumes/<id>/generate-questions/ → Generate new question set
  GET  /api/resumes/<id>/questions/          → List all question sets for resume
  GET  /api/resumes/<id>/questions/<qs_id>/  → Retrieve a specific question set
"""
import logging

from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.resumes.models import Resume

from .models import InterviewQuestionSet
from .serializers import (
    GenerateQuestionsRequestSerializer,
    InterviewQuestionSetSerializer,
)
from .services import InterviewGeneratorService

logger = logging.getLogger(__name__)


def _get_user_resume(pk: int, user) -> Resume | None:
    """Return Resume if it exists and belongs to the authenticated user."""
    try:
        return Resume.objects.get(pk=pk, user=user)
    except Resume.DoesNotExist:
        return None


class GenerateQuestionsView(APIView):
    """
    POST /api/resumes/<pk>/generate-questions/

    Generate a new AI interview question set for the given resume.

    Request Body:
        {
            "difficulty": "Medium",    // Easy | Medium | Hard
            "count": 10,               // 5 | 10 | 20 | 30
            "role": "Backend Developer"
        }

    Response 201:
        {
            "message": "...",
            "data": { id, resume, job_role, difficulty, question_count, questions, provider, created_at }
        }
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser]

    def post(self, request, pk: int) -> Response:
        # ── Auth check ───────────────────────────────────────────────────────
        resume = _get_user_resume(pk, request.user)
        if not resume:
            return Response(
                {"detail": "Resume not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # ── Validate request body ────────────────────────────────────────────
        req_serializer = GenerateQuestionsRequestSerializer(data=request.data)
        if not req_serializer.is_valid():
            return Response(
                {"detail": "Invalid request.", "errors": req_serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        difficulty = req_serializer.validated_data["difficulty"]
        count = req_serializer.validated_data["count"]
        job_role = req_serializer.validated_data["role"]

        # ── Generate ─────────────────────────────────────────────────────────
        try:
            question_set = InterviewGeneratorService.generate(
                resume=resume,
                job_role=job_role,
                difficulty=difficulty,
                count=count,
            )
        except Exception as exc:
            logger.error(f"Interview question generation failed for resume #{pk}: {exc}")
            return Response(
                {"detail": f"Question generation failed: {str(exc)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        serializer = InterviewQuestionSetSerializer(question_set)
        return Response(
            {
                "message": f"Generated {question_set.question_count} {difficulty} interview questions for '{job_role}'.",
                "data": serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )


class QuestionSetListView(APIView):
    """
    GET /api/resumes/<pk>/questions/

    List all interview question sets for the given resume, newest first.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk: int) -> Response:
        resume = _get_user_resume(pk, request.user)
        if not resume:
            return Response(
                {"detail": "Resume not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        question_sets = InterviewGeneratorService.get_all(resume)
        serializer = InterviewQuestionSetSerializer(question_sets, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class QuestionSetDetailView(APIView):
    """
    GET /api/resumes/<pk>/questions/<qs_id>/

    Retrieve a specific interview question set by ID.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk: int, qs_id: int) -> Response:
        resume = _get_user_resume(pk, request.user)
        if not resume:
            return Response(
                {"detail": "Resume not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            question_set = InterviewQuestionSet.objects.get(pk=qs_id, resume=resume)
        except InterviewQuestionSet.DoesNotExist:
            return Response(
                {"detail": "Interview question set not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = InterviewQuestionSetSerializer(question_set)
        return Response(serializer.data, status=status.HTTP_200_OK)
