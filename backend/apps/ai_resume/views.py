"""
apps/ai_resume/views.py

API Views for the AI Resume Improvement Suggestions module:
  POST /api/resumes/<id>/ai-suggestions/ → AISuggestionView (generate AI suggestions)
  GET  /api/resumes/<id>/ai-suggestions/ → AISuggestionView (retrieve saved suggestions)
"""
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.resumes.models import Resume
from .models import ResumeSuggestion
from .serializers import ResumeSuggestionSerializer
from .services import AISuggestionService


def _get_user_resume(pk: int, user) -> Resume | None:
    """Return Resume if exists and belongs to user."""
    try:
        return Resume.objects.get(pk=pk, user=user)
    except Resume.DoesNotExist:
        return None


class AISuggestionView(APIView):
    """
    POST /api/resumes/<id>/ai-suggestions/ — Generate (or refresh) AI suggestions.
    GET  /api/resumes/<id>/ai-suggestions/ — Retrieve existing saved AI suggestions.
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser]

    def post(self, request, pk: int) -> Response:
        resume = _get_user_resume(pk, request.user)
        if not resume:
            return Response(
                {"detail": "Resume not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            suggestions_obj = AISuggestionService.generate_suggestions(resume)
            serializer = ResumeSuggestionSerializer(suggestions_obj)
            return Response(
                {
                    "message": "AI Resume Improvement suggestions generated successfully.",
                    "data": serializer.data,
                },
                status=status.HTTP_201_CREATED,
            )
        except Exception as exc:
            return Response(
                {"detail": f"AI Suggestion generation failed: {str(exc)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def get(self, request, pk: int) -> Response:
        resume = _get_user_resume(pk, request.user)
        if not resume:
            return Response(
                {"detail": "Resume not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            suggestions_obj = resume.ai_suggestions
            serializer = ResumeSuggestionSerializer(suggestions_obj)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ResumeSuggestion.DoesNotExist:
            # If not yet generated, attempt calculation
            try:
                suggestions_obj = AISuggestionService.generate_suggestions(resume)
                serializer = ResumeSuggestionSerializer(suggestions_obj)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except Exception as exc:
                return Response(
                    {"detail": f"AI Suggestions not found and generation failed: {str(exc)}"},
                    status=status.HTTP_404_NOT_FOUND,
                )
