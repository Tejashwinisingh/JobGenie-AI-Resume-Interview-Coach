"""
apps/interview_evaluation/constants.py

Constants for Module 10 — AI Answer Evaluation & Interview Analysis Engine.
"""

# ─── Hiring Recommendation Choices ──────────────────────────────────────────
REC_HIGHLY_RECOMMENDED = "Highly Recommended"
REC_RECOMMENDED = "Recommended"
REC_NEEDS_IMPROVEMENT = "Needs Improvement"
REC_NOT_RECOMMENDED = "Not Recommended"

HIRING_RECOMMENDATION_CHOICES = [
    (REC_HIGHLY_RECOMMENDED, "Highly Recommended"),
    (REC_RECOMMENDED, "Recommended"),
    (REC_NEEDS_IMPROVEMENT, "Needs Improvement"),
    (REC_NOT_RECOMMENDED, "Not Recommended"),
]

# ─── Score Thresholds for Hiring Recommendations ─────────────────────────────
THRESHOLD_HIGHLY_RECOMMENDED = 85
THRESHOLD_RECOMMENDED = 70
THRESHOLD_NEEDS_IMPROVEMENT = 50

# ─── OpenRouter / OpenAI Config ─────────────────────────────────────────────
DEFAULT_EVALUATION_MODEL = "meta-llama/llama-3.1-8b-instruct:free"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
EVALUATION_TIMEOUT_SECONDS = 90
