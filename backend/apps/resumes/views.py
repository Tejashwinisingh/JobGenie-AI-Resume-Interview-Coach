"""
apps/resumes/views.py

API Views for the resumes module:
  GET    /api/resumes/             → ResumeListCreateView  (list user's resumes)
  POST   /api/resumes/             → ResumeListCreateView  (upload new resume & auto-process)
  DELETE /api/resumes/<id>/        → ResumeDetailView      (delete a resume)
  PUT    /api/resumes/<id>/        → ResumeDetailView      (replace a resume & auto-process)
  POST   /api/resumes/<id>/process/→ ResumeProcessView     (extract and clean resume text)
  GET    /api/resumes/<id>/text/   → ResumeTextView        (retrieve raw and cleaned text)
  POST   /api/resumes/<id>/parse/  → ResumeParseView       (parse cleaned text into structured data)
  GET    /api/resumes/<id>/parsed/ → ResumeParsedDataView  (retrieve structured parsed data)
"""
import os
# pyrefly: ignore [missing-import]
from rest_framework import status
# pyrefly: ignore [missing-import]
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
# pyrefly: ignore [missing-import]
from rest_framework.permissions import IsAuthenticated
# pyrefly: ignore [missing-import]
from rest_framework.response import Response
# pyrefly: ignore [missing-import]
from rest_framework.views import APIView

from .models import Resume, ParsedResume
from .serializers import (
    ResumeUploadSerializer,
    ResumeListSerializer,
    ResumeTextDetailSerializer,
    ParsedResumeSerializer,
    ALLOWED_EXTENSIONS,
)
from .services import ResumeTextExtractorService


# ─── Helper ───────────────────────────────────────────────────────────────────

def _get_user_resume(pk, user):
    """Return the resume if it exists and belongs to user, else None."""
    try:
        return Resume.objects.get(pk=pk, user=user)
    except Resume.DoesNotExist:
        return None


# ─── List & Create ────────────────────────────────────────────────────────────

class ResumeListCreateView(APIView):
    """
    GET  /api/resumes/  – List all resumes belonging to the authenticated user.
    POST /api/resumes/  – Upload a new resume (PDF or DOCX, max 5 MB) & extract text.
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        resumes = Resume.objects.filter(user=request.user)
        serializer = ResumeListSerializer(resumes, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = ResumeUploadSerializer(
            data=request.data,
            context={'request': request},
        )
        if serializer.is_valid():
            resume = serializer.save()

            # Auto-trigger text extraction, cleaning, and structured parsing
            try:
                ResumeTextExtractorService.process_resume(resume)
            except Exception:
                pass

            response_serializer = ResumeListSerializer(resume, context={'request': request})
            return Response(
                {
                    'message': 'Resume uploaded, processed, and parsed successfully.',
                    'resume': response_serializer.data,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ─── Detail (Delete & Replace) ────────────────────────────────────────────────

class ResumeDetailView(APIView):
    """
    DELETE /api/resumes/<id>/  – Delete a specific resume.
    PUT    /api/resumes/<id>/  – Replace a resume with a new file & re-extract text.
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def delete(self, request, pk):
        resume = _get_user_resume(pk, request.user)
        if not resume:
            return Response(
                {'detail': 'Resume not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        resume.delete()
        return Response(
            {'message': 'Resume deleted successfully.'},
            status=status.HTTP_200_OK,
        )

    def put(self, request, pk):
        """Replace the existing resume file with a newly uploaded one."""
        resume = _get_user_resume(pk, request.user)
        if not resume:
            return Response(
                {'detail': 'Resume not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ResumeUploadSerializer(
            data=request.data,
            context={'request': request},
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if resume.file:
            storage = resume.file.storage
            old_path = resume.file.name
            if storage.exists(old_path):
                storage.delete(old_path)

        uploaded_file = serializer.validated_data['file']
        _, ext = os.path.splitext(uploaded_file.name.lower())
        file_type = ALLOWED_EXTENSIONS[ext]

        resume.original_filename = uploaded_file.name
        resume.file = uploaded_file
        resume.file_type = file_type
        resume.file_size = uploaded_file.size
        resume.processing_status = Resume.STATUS_PENDING
        resume.raw_text = None
        resume.cleaned_text = None
        resume.processing_error = None
        resume.processed_at = None
        resume.save()

        # Delete existing parsed data if present
        if hasattr(resume, 'parsed_data'):
            resume.parsed_data.delete()

        try:
            ResumeTextExtractorService.process_resume(resume)
        except Exception:
            pass

        response_serializer = ResumeListSerializer(resume, context={'request': request})
        return Response(
            {
                'message': 'Resume replaced and processed successfully.',
                'resume': response_serializer.data,
            },
            status=status.HTTP_200_OK,
        )


# ─── Process Endpoint ──────────────────────────────────────────────────────────

class ResumeProcessView(APIView):
    """
    POST /api/resumes/<id>/process/
    Trigger text extraction, cleaning, and structured parsing for a specific resume.
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def post(self, request, pk):
        resume = _get_user_resume(pk, request.user)
        if not resume:
            return Response(
                {'detail': 'Resume not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            ResumeTextExtractorService.process_resume(resume)
            serializer = ResumeTextDetailSerializer(resume)
            return Response(
                {
                    'message': 'Resume text processed successfully.',
                    'data': serializer.data,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as exc:
            return Response(
                {
                    'detail': f'Text extraction failed: {str(exc)}',
                    'processing_status': resume.processing_status,
                    'processing_error': resume.processing_error,
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# ─── Get Extracted Text Endpoint ──────────────────────────────────────────────

class ResumeTextView(APIView):
    """
    GET /api/resumes/<id>/text/
    Retrieve raw text, cleaned text, and processing metadata for a resume.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        resume = _get_user_resume(pk, request.user)
        if not resume:
            return Response(
                {'detail': 'Resume not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ResumeTextDetailSerializer(resume)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ─── Module 4 – Resume Parse Endpoint ─────────────────────────────────────────

class ResumeParseView(APIView):
    """
    POST /api/resumes/<id>/parse/
    Trigger structured parsing for a resume's extracted text.
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def post(self, request, pk):
        resume = _get_user_resume(pk, request.user)
        if not resume:
            return Response(
                {'detail': 'Resume not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not resume.cleaned_text and not resume.raw_text:
            return Response(
                {'detail': 'Resume text has not been extracted yet. Run /process/ first.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            parsed_instance = ResumeTextExtractorService.parse_and_store_resume(resume)
            serializer = ParsedResumeSerializer(parsed_instance)
            return Response(
                {
                    'message': 'Resume parsed into structured data successfully.',
                    'data': serializer.data,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as exc:
            return Response(
                {'detail': f'Parsing failed: {str(exc)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# ─── Module 4 – Get Parsed Data Endpoint ──────────────────────────────────────

class ResumeParsedDataView(APIView):
    """
    GET /api/resumes/<id>/parsed/
    Retrieve structured parsed resume data (skills, contact, experience, etc.).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        resume = _get_user_resume(pk, request.user)
        if not resume:
            return Response(
                {'detail': 'Resume not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not hasattr(resume, 'parsed_data') or resume.parsed_data is None:
            # If not yet parsed but text exists, trigger parse
            if resume.cleaned_text or resume.raw_text:
                parsed_instance = ResumeTextExtractorService.parse_and_store_resume(resume)
            else:
                return Response(
                    {'detail': 'Parsed data not available. Process the resume first.'},
                    status=status.HTTP_404_NOT_FOUND,
                )
        else:
            parsed_instance = resume.parsed_data

        serializer = ParsedResumeSerializer(parsed_instance)
        return Response(serializer.data, status=status.HTTP_200_OK)
