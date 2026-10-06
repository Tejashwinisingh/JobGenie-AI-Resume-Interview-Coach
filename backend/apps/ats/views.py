"""
apps/ats/views.py

API Views for the ATS module:

  POST /api/resumes/<id>/ats-score/  → ATSScoreView  (generate / refresh score)
  GET  /api/resumes/<id>/ats-score/  → ATSScoreView  (retrieve existing score)

Error handling:
  - 404: Resume not found or not owned by user
  - 400: Resume not yet processed (no extracted text)
  - 400: Resume not yet parsed (parsed_data missing — triggers auto-parse if possible)
  - 500: Unexpected engine errors
"""
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.resumes.models import Resume
from apps.resumes.services import ResumeTextExtractorService
from .models import ATSScore
from .serializers import ATSScoreSerializer
from .services import ATSService


def _get_user_resume(pk: int, user) -> Resume | None:
    """Return the resume if it exists and belongs to user, else None."""
    try:
        return Resume.objects.get(pk=pk, user=user)
    except Resume.DoesNotExist:
        return None


class ATSScoreView(APIView):
    """
    POST /api/resumes/<id>/ats-score/ — Generate (or refresh) ATS score.
    GET  /api/resumes/<id>/ats-score/ — Retrieve existing ATS score.
    """

    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser]

    # ── POST: generate / refresh ───────────────────────────────────────────
    def post(self, request, pk: int) -> Response:
        """
        Trigger ATS evaluation for the specified resume.

        Auto-triggers text extraction and parsing if not yet done.

        Returns:
            201: ATS score generated successfully.
            400: Resume not processed or no text available.
            404: Resume not found.
            500: Internal evaluation error.
        """
        resume = _get_user_resume(pk, request.user)
        if not resume:
            return Response(
                {"detail": "Resume not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Ensure text has been extracted
        if not (resume.cleaned_text or resume.raw_text):
            if resume.processing_status in (Resume.STATUS_PENDING, Resume.STATUS_FAILED):
                # Attempt auto-extraction
                try:
                    ResumeTextExtractorService.process_resume(resume)
                    resume.refresh_from_db()
                except Exception as exc:
                    return Response(
                        {
                            "detail": (
                                "Resume text extraction failed. "
                                f"Please process the resume first. ({exc})"
                            )
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            else:
                return Response(
                    {
                        "detail": (
                            "Resume has not been processed yet. "
                            "Call POST /api/resumes/<id>/process/ first."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Ensure parsed data exists (auto-trigger if missing)
        if not hasattr(resume, "parsed_data") or resume.parsed_data is None:
            try:
                ResumeTextExtractorService.parse_and_store_resume(resume)
                resume.refresh_from_db()
            except Exception:
                pass  # ATS engine handles missing parsed_data gracefully

        # Run ATS evaluation
        try:
            ats_score_obj = ATSService.evaluate(resume)
            serializer = ATSScoreSerializer(ats_score_obj)
            return Response(
                {
                    "message": "ATS score generated successfully.",
                    "data": serializer.data,
                },
                status=status.HTTP_201_CREATED,
            )
        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as exc:
            return Response(
                {"detail": f"ATS evaluation failed: {str(exc)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    # ── GET: retrieve ──────────────────────────────────────────────────────
    def get(self, request, pk: int) -> Response:
        """
        Retrieve the existing ATS score for a resume.

        If no score exists but the resume is processed, triggers evaluation.

        Returns:
            200: ATS score retrieved successfully.
            404: Resume not found or not yet scored.
        """
        resume = _get_user_resume(pk, request.user)
        if not resume:
            return Response(
                {"detail": "Resume not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Try to retrieve existing score
        try:
            ats_score_obj = resume.ats_score
            serializer = ATSScoreSerializer(ats_score_obj)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ATSScore.DoesNotExist:
            pass

        # Score not yet generated — evaluate if possible
        if resume.cleaned_text or resume.raw_text:
            try:
                ats_score_obj = ATSService.evaluate(resume)
                serializer = ATSScoreSerializer(ats_score_obj)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except Exception as exc:
                return Response(
                    {"detail": f"ATS evaluation failed: {str(exc)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        return Response(
            {
                "detail": (
                    "ATS score not yet generated for this resume. "
                    "Call POST /api/resumes/<id>/ats-score/ to generate it."
                )
            },
            status=status.HTTP_404_NOT_FOUND,
        )
