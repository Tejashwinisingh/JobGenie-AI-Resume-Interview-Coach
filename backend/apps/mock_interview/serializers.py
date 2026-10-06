"""
apps/mock_interview/serializers.py

Serializers for Module 9 — AI Mock Interview System.
"""
from rest_framework import serializers

from .constants import (
    DEFAULT_QUESTION_COUNT,
    DIFFICULTY_CHOICES,
    DIFFICULTY_MEDIUM,
    INTERVIEW_TYPE_CHOICES,
    MAX_QUESTION_COUNT,
    MIN_QUESTION_COUNT,
    TYPE_MIXED,
    VALID_QUESTION_COUNTS,
)
from .models import InterviewQuestion, InterviewSession


class StartInterviewRequestSerializer(serializers.Serializer):
    """
    Validates request payload for POST /api/interviews/start/
    """
    resume_id = serializers.IntegerField(
        required=True,
        help_text="ID of the uploaded resume.",
    )
    job_description_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        default=None,
        help_text="Optional ID of a Job Description.",
    )
    role = serializers.CharField(
        max_length=200,
        default="Python Developer",
        help_text="Target role (e.g. Backend Developer, Java Developer, Software Engineer).",
    )
    difficulty = serializers.ChoiceField(
        choices=[c[0] for c in DIFFICULTY_CHOICES],
        default=DIFFICULTY_MEDIUM,
        help_text="Difficulty level: Easy | Medium | Hard",
    )
    interview_type = serializers.ChoiceField(
        choices=[c[0] for c in INTERVIEW_TYPE_CHOICES],
        default=TYPE_MIXED,
        help_text="Interview type: HR | Technical | Behavioral | Coding | Project Discussion | Mixed",
    )
    question_count = serializers.IntegerField(
        default=DEFAULT_QUESTION_COUNT,
        min_value=MIN_QUESTION_COUNT,
        max_value=MAX_QUESTION_COUNT,
        help_text=f"Total questions. Default {DEFAULT_QUESTION_COUNT}.",
    )

    def validate_question_count(self, value: int) -> int:
        """Ensure question_count is within bounds 1 to 30."""
        if value < MIN_QUESTION_COUNT:
            return MIN_QUESTION_COUNT
        if value > MAX_QUESTION_COUNT:
            return MAX_QUESTION_COUNT
        return value


class SubmitAnswerRequestSerializer(serializers.Serializer):
    """
    Validates request payload for POST /api/interviews/{session_id}/answer/
    """
    answer = serializers.CharField(
        required=True,
        allow_blank=False,
        trim_whitespace=True,
        help_text="The candidate's response to the current question.",
    )

    def validate_answer(self, value: str) -> str:
        if not value or not value.strip():
            raise serializers.ValidationError("Answer cannot be blank.")
        return value.strip()


class InterviewQuestionSerializer(serializers.ModelSerializer):
    """Serializer for an individual question/answer pair."""

    class Meta:
        model = InterviewQuestion
        fields = [
            "id",
            "question_number",
            "category",
            "question",
            "user_answer",
            "answered_at",
            "created_at",
        ]
        read_only_fields = fields


class InterviewSessionSerializer(serializers.ModelSerializer):
    """Full detail serializer for an InterviewSession."""
    questions = InterviewQuestionSerializer(many=True, read_only=True)
    remaining_questions = serializers.ReadOnlyField()
    progress = serializers.ReadOnlyField()

    class Meta:
        model = InterviewSession
        fields = [
            "id",
            "resume",
            "job_description",
            "role",
            "difficulty",
            "interview_type",
            "status",
            "current_question",
            "total_questions",
            "completed_questions",
            "remaining_questions",
            "progress",
            "started_at",
            "completed_at",
            "questions",
        ]
        read_only_fields = fields


class InterviewSessionSummarySerializer(serializers.ModelSerializer):
    """Summary serializer for listing interview sessions."""
    remaining_questions = serializers.ReadOnlyField()
    progress = serializers.ReadOnlyField()

    class Meta:
        model = InterviewSession
        fields = [
            "id",
            "resume",
            "job_description",
            "role",
            "difficulty",
            "interview_type",
            "status",
            "current_question",
            "total_questions",
            "completed_questions",
            "remaining_questions",
            "progress",
            "started_at",
            "completed_at",
        ]
        read_only_fields = fields
