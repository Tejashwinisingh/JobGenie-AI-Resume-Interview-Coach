"""
apps/interview_evaluation/serializers.py

Serializers for Module 10 — AI Answer Evaluation & Interview Analysis Engine.
"""
from rest_framework import serializers

from .models import InterviewEvaluation


class InterviewEvaluationSerializer(serializers.ModelSerializer):
    """
    Serializer for full InterviewEvaluation reports.
    """
    session_id = serializers.IntegerField(source="session.id", read_only=True)
    role = serializers.CharField(source="session.role", read_only=True)
    difficulty = serializers.CharField(source="session.difficulty", read_only=True)
    interview_type = serializers.CharField(source="session.interview_type", read_only=True)

    class Meta:
        model = InterviewEvaluation
        fields = [
            "id",
            "session_id",
            "role",
            "difficulty",
            "interview_type",
            "overall_score",
            "technical_score",
            "communication_score",
            "confidence_score",
            "grammar_score",
            "problem_solving_score",
            "professionalism_score",
            "average_response_length",
            "interview_duration",
            "hiring_recommendation",
            "summary",
            "strengths",
            "weaknesses",
            "recommended_topics",
            "question_analysis",
            "created_at",
        ]
        read_only_fields = fields
