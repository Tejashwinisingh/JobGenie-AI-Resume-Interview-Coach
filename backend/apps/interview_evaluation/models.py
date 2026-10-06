"""
apps/interview_evaluation/models.py

Models for Module 10 — AI Answer Evaluation & Interview Analysis Engine.
Designed to be reusable by future Analytics, Career Coach, and Learning Recommendation modules.
"""
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from .constants import (
    HIRING_RECOMMENDATION_CHOICES,
    REC_RECOMMENDED,
)


class InterviewEvaluation(models.Model):
    """
    Stores comprehensive evaluation results for a completed mock interview session.
    """

    session = models.OneToOneField(
        "mock_interview.InterviewSession",
        on_delete=models.CASCADE,
        related_name="evaluation",
        help_text="The completed interview session being evaluated.",
    )
    overall_score = models.PositiveIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Overall weighted score (0–100).",
    )
    technical_score = models.PositiveIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Technical knowledge and accuracy score (0–100).",
    )
    communication_score = models.PositiveIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Communication clarity and articulation score (0–100).",
    )
    confidence_score = models.PositiveIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Confidence and composure score (0–100).",
    )
    grammar_score = models.PositiveIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Language, grammar, and vocabulary accuracy score (0–100).",
    )
    problem_solving_score = models.PositiveIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Problem solving and architectural reasoning score (0–100).",
    )
    professionalism_score = models.PositiveIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Professional conduct and STAR methodology score (0–100).",
    )
    average_response_length = models.PositiveIntegerField(
        default=0,
        help_text="Average word count per candidate response.",
    )
    interview_duration = models.CharField(
        max_length=50,
        default="0m 0s",
        help_text="Total elapsed duration of the interview session.",
    )
    hiring_recommendation = models.CharField(
        max_length=50,
        choices=HIRING_RECOMMENDATION_CHOICES,
        default=REC_RECOMMENDED,
        db_index=True,
        help_text="Hiring decision: Highly Recommended | Recommended | Needs Improvement | Not Recommended",
    )
    summary = models.TextField(
        help_text="Executive summary of candidate performance.",
    )
    strengths = models.JSONField(
        default=list,
        help_text="List of identified candidate strengths.",
    )
    weaknesses = models.JSONField(
        default=list,
        help_text="List of areas needing improvement.",
    )
    recommended_topics = models.JSONField(
        default=list,
        help_text="List of priority study/learning topics.",
    )
    question_analysis = models.JSONField(
        default=list,
        help_text="Detailed per-question score breakdown and feedback.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "interview_evaluation"
        verbose_name = "Interview Evaluation"
        verbose_name_plural = "Interview Evaluations"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Evaluation for Session #{self.session_id} | Score: {self.overall_score}/100 ({self.hiring_recommendation})"
