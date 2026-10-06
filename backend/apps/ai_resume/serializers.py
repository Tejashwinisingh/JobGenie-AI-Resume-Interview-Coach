"""
apps/ai_resume/serializers.py

Serializer for AI Resume Improvement Suggestions API output.
"""
from rest_framework import serializers

from .models import ResumeSuggestion


class ResumeSuggestionSerializer(serializers.ModelSerializer):
    """
    Serializes ResumeSuggestion model matching specified API output format:
    {
        "summary": "...",
        "strengths": [...],
        "weaknesses": [...],
        "suggestions": [...],
        "priority_skills": [...],
        "improved_project_description": "..."
    }
    """

    class Meta:
        model = ResumeSuggestion
        fields = [
            "summary",
            "strengths",
            "weaknesses",
            "suggestions",
            "priority_skills",
            "improved_project_description",
            "created_at",
        ]
        read_only_fields = fields
