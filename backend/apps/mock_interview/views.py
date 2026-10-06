"""
apps/mock_interview/views.py

API Views for Module 9 — AI Mock Interview System:
  POST /api/interviews/start/          → Start a new mock interview session
  POST /api/interviews/<id>/answer/     → Submit candidate answer & get next question
  GET  /api/interviews/<id>/            → Retrieve session state & progress
  POST /api/interviews/<id>/finish/     → End interview session early
  GET  /api/interviews/                 → List candidate's interview sessions
"""
import logging

from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.job_matching.models import JobDescription
from apps.resumes.models import Resume

from .models import InterviewSession
from .serializers import (
    InterviewSessionSerializer,
    InterviewSessionSummarySerializer,
    StartInterviewRequestSerializer,
    SubmitAnswerRequestSerializer,
)
from .services import MockInterviewService

logger = logging.getLogger(__name__)


def _get_user_session(session_id: int, user) -> InterviewSession | None:
    """Retrieve session if it exists and belongs to the authenticated user."""
    try:
        return InterviewSession.objects.get(pk=session_id, user=user)
    except InterviewSession.DoesNotExist:
        return None


class StartInterviewView(APIView):
    """
    POST /api/interviews/start/

    Initialize a new mock interview session and return Question #1.

    Body:
    {
        "resume_id": 1,
        "job_description_id": 1,   // optional
        "role": "Python Developer",
        "difficulty": "Medium",
        "interview_type": "Mixed",
        "question_count": 10
    }
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser]

    def post(self, request) -> Response:
        serializer = StartInterviewRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"detail": "Invalid request.", "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        resume_id = serializer.validated_data["resume_id"]
        jd_id = serializer.validated_data.get("job_description_id")
        role = serializer.validated_data["role"]
        difficulty = serializer.validated_data["difficulty"]
        interview_type = serializer.validated_data["interview_type"]
        question_count = serializer.validated_data["question_count"]

        # Validate Resume ownership
        try:
            resume = Resume.objects.get(pk=resume_id, user=request.user)
        except Resume.DoesNotExist:
            return Response(
                {"detail": "Resume not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Validate Job Description ownership (if provided)
        job_description = None
        if jd_id:
            try:
                job_description = JobDescription.objects.get(pk=jd_id, user=request.user)
            except JobDescription.DoesNotExist:
                return Response(
                    {"detail": "Job Description not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )

        try:
            session, q1 = MockInterviewService.start_session(
                user=request.user,
                resume=resume,
                job_description=job_description,
                role=role,
                difficulty=difficulty,
                interview_type=interview_type,
                question_count=question_count,
            )
            return Response(
                {
                    "session_id": session.id,
                    "question_number": q1.question_number,
                    "category": q1.category,
                    "question": q1.question,
                    "total_questions": session.total_questions,
                    "status": session.status,
                },
                status=status.HTTP_201_CREATED,
            )
        except Exception as exc:
            logger.error(f"Failed to start interview for user {request.user.email}: {exc}")
            return Response(
                {"detail": f"Failed to start interview session: {str(exc)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class SubmitAnswerView(APIView):
    """
    POST /api/interviews/<session_id>/answer/

    Submit an answer for the current question and receive the next question.

    Body:
    {
        "answer": "I built a REST API using Django REST framework..."
    }
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser]

    def post(self, request, session_id: int) -> Response:
        session = _get_user_session(session_id, request.user)
        if not session:
            return Response(
                {"detail": "Interview Session not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if session.status == "completed":
            return Response(
                {"detail": "Interview already completed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = SubmitAnswerRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"detail": "Invalid answer.", "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        answer_text = serializer.validated_data["answer"]

        try:
            result = MockInterviewService.submit_answer(session, answer_text)

            if result["is_completed"]:
                return Response(
                    {
                        "session_id": session.id,
                        "status": "Completed",
                        "is_completed": True,
                        "message": "Interview completed successfully.",
                        "completed_questions": session.completed_questions,
                        "total_questions": session.total_questions,
                    },
                    status=status.HTTP_200_OK,
                )

            next_q = result["next_question"]
            return Response(
                {
                    "session_id": session.id,
                    "status": "In Progress",
                    "is_completed": False,
                    "question_number": next_q.question_number,
                    "category": next_q.category,
                    "question": next_q.question,
                    "completed_questions": session.completed_questions,
                    "total_questions": session.total_questions,
                    "progress": session.progress,
                },
                status=status.HTTP_200_OK,
            )
        except ValueError as val_err:
            return Response(
                {"detail": str(val_err)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as exc:
            logger.error(f"Error submitting answer for session #{session_id}: {exc}")
            return Response(
                {"detail": f"Failed to submit answer: {str(exc)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class InterviewSessionDetailView(APIView):
    """
    GET /api/interviews/<session_id>/

    Retrieve complete status, progress, and stored Q&As for an interview session.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, session_id: int) -> Response:
        session = _get_user_session(session_id, request.user)
        if not session:
            return Response(
                {"detail": "Interview Session not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = InterviewSessionSerializer(session)
        return Response(serializer.data, status=status.HTTP_200_OK)


class FinishInterviewView(APIView):
    """
    POST /api/interviews/<session_id>/finish/

    Manually end an interview session early.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, session_id: int) -> Response:
        session = _get_user_session(session_id, request.user)
        if not session:
            return Response(
                {"detail": "Interview Session not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        session = MockInterviewService.finish_session(session)
        return Response(
            {
                "session_id": session.id,
                "status": "Completed",
                "message": "Interview completed successfully.",
                "completed_questions": session.completed_questions,
                "total_questions": session.total_questions,
            },
            status=status.HTTP_200_OK,
        )


class InterviewSessionListView(APIView):
    """
    GET /api/interviews/

    List all interview sessions for the authenticated user, newest first.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request) -> Response:
        sessions = InterviewSession.objects.filter(user=request.user).order_by("-started_at")
        serializer = InterviewSessionSummarySerializer(sessions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
