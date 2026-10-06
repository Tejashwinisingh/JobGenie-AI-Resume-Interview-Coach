"""
apps/interview_generator/serializers.py

Serializers for the Interview Question Generator module.
"""
from rest_framework import serializers

from .constants import (
    DEFAULT_QUESTION_COUNT,
    DIFFICULTY_CHOICES,
    DIFFICULTY_MEDIUM,
    MAX_QUESTION_COUNT,
    VALID_QUESTION_COUNTS,
)
from .models import InterviewQuestionSet


class QuestionItemSerializer(serializers.Serializer):
    """Serializer for a single interview question item."""
    id = serializers.IntegerField()
    category = serializers.CharField()
    question = serializers.CharField()


class InterviewQuestionSetSerializer(serializers.ModelSerializer):
    """Full serializer for a saved InterviewQuestionSet."""
    questions = QuestionItemSerializer(many=True, read_only=True)

    class Meta:
        model = InterviewQuestionSet
        fields = [
            "id",
            "resume",
            "job_role",
            "difficulty",
            "question_count",
            "questions",
            "provider",
            "created_at",
        ]
        read_only_fields = fields


class GenerateQuestionsRequestSerializer(serializers.Serializer):
    """
    Validates the POST body for /api/resumes/<id>/generate-questions/

    Example body:
    {
        "difficulty": "Medium",
        "count": 10,
        "role": "Backend Developer"
    }
    """
    difficulty = serializers.ChoiceField(
        choices=[c[0] for c in DIFFICULTY_CHOICES],
        default=DIFFICULTY_MEDIUM,
        help_text="Interview difficulty: Easy | Medium | Hard",
    )
    count = serializers.IntegerField(
        default=DEFAULT_QUESTION_COUNT,
        min_value=5,
        max_value=MAX_QUESTION_COUNT,
        help_text=f"Number of questions to generate. Allowed: {VALID_QUESTION_COUNTS}",
    )
    role = serializers.CharField(
        max_length=200,
        default="Software Developer",
        help_text="Target job role (e.g. Backend Developer, Full Stack Engineer).",
    )

    def validate_count(self, value: int) -> int:
        """Snap count to the nearest supported value."""
        if value not in VALID_QUESTION_COUNTS:
            # Snap to nearest valid count
            nearest = min(VALID_QUESTION_COUNTS, key=lambda x: abs(x - value))
            return nearest
        return value
