"""
apps/resumes/serializers.py

Serializers for the resumes module:
  - ResumeUploadSerializer      : validate & create a new upload
  - ResumeListSerializer        : read-only representation of a resume
  - ResumeTextDetailSerializer  : detailed view including extracted raw/cleaned text
  - ParsedResumeSerializer      : structured representation of parsed resume data
"""
import os
# pyrefly: ignore [missing-import]
from rest_framework import serializers

from .models import Resume, ParsedResume

# ─── Constants ────────────────────────────────────────────────────────────────

MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB

ALLOWED_MIME_TYPES = {
    'application/pdf': Resume.FILE_TYPE_PDF,
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': Resume.FILE_TYPE_DOCX,
}

ALLOWED_EXTENSIONS = {
    '.pdf':  Resume.FILE_TYPE_PDF,
    '.docx': Resume.FILE_TYPE_DOCX,
}


# ─── List / Read serializer ───────────────────────────────────────────────────

class ResumeListSerializer(serializers.ModelSerializer):
    """Read-only serializer used when listing resumes."""
    file_url = serializers.SerializerMethodField()
    file_size_kb = serializers.SerializerMethodField()
    has_extracted_text = serializers.SerializerMethodField()
    has_parsed_data = serializers.SerializerMethodField()

    class Meta:
        model = Resume
        fields = (
            'id',
            'original_filename',
            'file_type',
            'file_size',
            'file_size_kb',
            'file_url',
            'uploaded_at',
            'processing_status',
            'processed_at',
            'has_extracted_text',
            'has_parsed_data',
            'processing_error',
        )
        read_only_fields = fields

    def get_file_url(self, obj):
        request = self.context.get('request')
        if request and obj.file:
            return request.build_absolute_uri(obj.file.url)
        return obj.file.url if obj.file else None

    def get_file_size_kb(self, obj):
        return round(obj.file_size / 1024, 1)

    def get_has_extracted_text(self, obj):
        return bool(obj.cleaned_text or obj.raw_text)

    def get_has_parsed_data(self, obj):
        return hasattr(obj, 'parsed_data') and obj.parsed_data is not None


# ─── Text Detail Serializer ──────────────────────────────────────────────────

class ResumeTextDetailSerializer(serializers.ModelSerializer):
    """Read-only serializer for retrieving extracted text details of a resume."""
    character_count = serializers.SerializerMethodField()
    word_count = serializers.SerializerMethodField()

    class Meta:
        model = Resume
        fields = (
            'id',
            'original_filename',
            'file_type',
            'processing_status',
            'raw_text',
            'cleaned_text',
            'processing_error',
            'processed_at',
            'character_count',
            'word_count',
        )
        read_only_fields = fields

    def get_character_count(self, obj):
        return len(obj.cleaned_text) if obj.cleaned_text else 0

    def get_word_count(self, obj):
        return len(obj.cleaned_text.split()) if obj.cleaned_text else 0


# ─── Parsed Data Serializer ──────────────────────────────────────────────────

class ParsedResumeSerializer(serializers.ModelSerializer):
    """Read-only serializer for retrieving structured parsed data of a resume."""

    class Meta:
        model = ParsedResume
        fields = (
            'id',
            'resume_id',
            'name',
            'email',
            'phone',
            'linkedin',
            'github',
            'skills',
            'education',
            'experience',
            'projects',
            'certifications',
            'parsed_at',
        )
        read_only_fields = fields


# ─── Upload / Write serializer ────────────────────────────────────────────────

class ResumeUploadSerializer(serializers.Serializer):
    """Validate and create a new resume upload."""
    file = serializers.FileField()

    def validate_file(self, uploaded_file):
        # ── Size check ────────────────────────────────────────────
        if uploaded_file.size > MAX_FILE_SIZE_BYTES:
            raise serializers.ValidationError(
                f'File too large. Maximum allowed size is 5 MB '
                f'(uploaded: {round(uploaded_file.size / 1024 / 1024, 2)} MB).'
            )

        # ── Extension check ───────────────────────────────────────
        _, ext = os.path.splitext(uploaded_file.name.lower())
        if ext not in ALLOWED_EXTENSIONS:
            raise serializers.ValidationError(
                f'Unsupported file type "{ext}". Only PDF and DOCX files are accepted.'
            )

        # ── Content-type check (defence in depth) ─────────────────
        content_type = getattr(uploaded_file, 'content_type', '')
        if content_type and content_type not in ALLOWED_MIME_TYPES:
            if content_type != 'application/octet-stream':
                raise serializers.ValidationError(
                    f'Unsupported MIME type "{content_type}". Only PDF and DOCX are accepted.'
                )

        return uploaded_file

    def create(self, validated_data):
        uploaded_file = validated_data['file']
        user = self.context['request'].user

        _, ext = os.path.splitext(uploaded_file.name.lower())
        file_type = ALLOWED_EXTENSIONS[ext]

        resume = Resume.objects.create(
            user=user,
            original_filename=uploaded_file.name,
            file=uploaded_file,
            file_type=file_type,
            file_size=uploaded_file.size,
        )
        return resume
