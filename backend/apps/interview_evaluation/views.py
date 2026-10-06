"""
apps/interview_evaluation/views.py

API Views for Module 10 — AI Answer Evaluation & Interview Analysis Engine:
  POST /api/interviews/<session_id>/evaluate/    → Generate evaluation report for completed session
  GET  /api/interviews/<session_id>/evaluation/  → Retrieve saved evaluation report
"""
import logging

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.mock_interview.models import InterviewSession

from .serializers import InterviewEvaluationSerializer
from .services import InterviewEvaluationService

logger = logging.getLogger(__name__)


def _get_user_session(session_id: int, user) -> InterviewSession | None:
    """Retrieve session if it exists and belongs to the authenticated user."""
    try:
        return InterviewSession.objects.get(pk=session_id, user=user)
    except InterviewSession.DoesNotExist:
        return None


class EvaluateInterviewSessionView(APIView):
    """
    POST /api/interviews/<session_id>/evaluate/

    Analyze all questions and answers from a completed interview session
    and generate a comprehensive evaluation report.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, session_id: int) -> Response:
        session = _get_user_session(session_id, request.user)
        if not session:
            return Response(
                {"detail": "Interview Session not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if session.status != "completed" and session.completed_questions < 1:
            return Response(
                {"detail": "Interview session is not completed yet. Please finish the interview first."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            evaluation = InterviewEvaluationService.evaluate_session(session)
            serializer = InterviewEvaluationSerializer(evaluation)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as exc:
            logger.error(f"Failed to evaluate InterviewSession #{session_id}: {exc}")
            return Response(
                {"detail": f"Evaluation failed: {str(exc)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class RetrieveInterviewEvaluationView(APIView):
    """
    GET /api/interviews/<session_id>/evaluation/

    Retrieve the saved evaluation report for an interview session.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, session_id: int) -> Response:
        session = _get_user_session(session_id, request.user)
        if not session:
            return Response(
                {"detail": "Interview Session not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        evaluation = InterviewEvaluationService.get_evaluation(session)
        if not evaluation:
            return Response(
                {"detail": "Evaluation report not found for this interview session. Run evaluation first."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = InterviewEvaluationSerializer(evaluation)
        return Response(serializer.data, status=status.HTTP_200_OK)
