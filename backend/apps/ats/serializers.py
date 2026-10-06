"""
apps/ats/serializers.py

Serializers for the ATS module API responses.
"""
from rest_framework import serializers

from .models import ATSScore


class ATSScoreSerializer(serializers.ModelSerializer):
    """
    Serializes a full ATS evaluation report.

    Output shape matches the spec:
    {
        "ats_score": 88,
        "grade": "A",
        "grade_label": "Very Good",
        "summary": "...",
        "breakdown": { "formatting": 14, ... },
        "analysis": {
            "technical_keywords_found": [...],
            "missing_sections": [...],
            "warnings": [...]
        },
        "evaluated_at": "2026-07-30T22:00:00Z"
    }
    """

    class Meta:
        model = ATSScore
        fields = [
            "ats_score",
            "grade",
            "grade_label",
            "summary",
            "breakdown",
            "analysis",
            "evaluated_at",
        ]
        read_only_fields = fields
