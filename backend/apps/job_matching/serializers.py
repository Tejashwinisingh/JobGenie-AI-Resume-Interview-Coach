"""
apps/job_matching/serializers.py

Serializers for Job Description Creation and Job Matching output.
"""
from rest_framework import serializers

from .models import JobDescription, JobMatch
from .constants import MAX_FILE_SIZE_BYTES, ALLOWED_EXTENSIONS


class JobDescriptionSerializer(serializers.ModelSerializer):
    """
    Serializes a JobDescription model instance.
    """

    class Meta:
        model = JobDescription
        fields = [
            "id",
            "title",
            "company",
            "description",
            "file",
            "file_type",
            "cleaned_text",
            "parsed_data",
            "created_at",
        ]
        read_only_fields = ["id", "file_type", "cleaned_text", "parsed_data", "created_at"]


class JobDescriptionCreateSerializer(serializers.Serializer):
    """
    Serializer for creating/uploading a new Job Description.
    Supports either pasted description text OR a PDF/DOCX file upload.
    """

    title = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")
    company = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")
    description = serializers.CharField(required=False, allow_blank=True, default="")
    file = serializers.FileField(required=False, allow_null=True)

    def validate(self, data):
        description = data.get("description", "").strip()
        file_obj = data.get("file")

        if not description and not file_obj:
            raise serializers.ValidationError(
                "Either a text description or a file upload (PDF/DOCX) must be provided."
            )

        if file_obj:
            import os
            _, ext = os.path.splitext(file_obj.name.lower())
            if ext not in ALLOWED_EXTENSIONS:
                raise serializers.ValidationError(
                    f"Unsupported file format '{ext}'. Only PDF (.pdf) and DOCX (.docx) files are accepted."
                )
            if file_obj.size > MAX_FILE_SIZE_BYTES:
                raise serializers.ValidationError(
                    "File size exceeds 5 MB limit."
                )

        return data


class JobMatchSerializer(serializers.ModelSerializer):
    """
    Serializes a JobMatch result into the exact specified output format:

    {
        "match_score": 82,
        "grade": "Very Good",
        "matched_skills": ["Java", "Spring Boot", "Docker"],
        "missing_skills": ["AWS", "Kafka", "REST API"],
        "extra_skills": ["React", "MySQL", "Git"],
        "experience_match": 18,
        "education_match": 8,
        "certification_match": 10,
        "keyword_match": 9
    }
    """

    experience_match = serializers.IntegerField(source="experience_score", read_only=True)
    education_match = serializers.IntegerField(source="education_score", read_only=True)
    certification_match = serializers.IntegerField(source="certification_score", read_only=True)
    keyword_match = serializers.IntegerField(source="keyword_score", read_only=True)

    class Meta:
        model = JobMatch
        fields = [
            "match_score",
            "grade",
            "matched_skills",
            "missing_skills",
            "extra_skills",
            "experience_match",
            "education_match",
            "certification_match",
            "keyword_match",
            "breakdown",
            "created_at",
        ]
        read_only_fields = fields
