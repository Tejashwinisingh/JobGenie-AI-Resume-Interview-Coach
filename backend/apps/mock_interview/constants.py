"""
apps/mock_interview/constants.py

Constants for Module 9 — AI Mock Interview System.
"""

# ─── Status Choices ──────────────────────────────────────────────────────────
STATUS_IN_PROGRESS = "in_progress"
STATUS_COMPLETED = "completed"
STATUS_ABANDONED = "abandoned"

STATUS_CHOICES = [
    (STATUS_IN_PROGRESS, "In Progress"),
    (STATUS_COMPLETED, "Completed"),
    (STATUS_ABANDONED, "Abandoned"),
]

# ─── Interview Types ─────────────────────────────────────────────────────────
TYPE_HR = "HR"
TYPE_TECHNICAL = "Technical"
TYPE_BEHAVIORAL = "Behavioral"
TYPE_CODING = "Coding"
TYPE_PROJECT = "Project Discussion"
TYPE_MIXED = "Mixed"

INTERVIEW_TYPE_CHOICES = [
    (TYPE_HR, "HR"),
    (TYPE_TECHNICAL, "Technical"),
    (TYPE_BEHAVIORAL, "Behavioral"),
    (TYPE_CODING, "Coding"),
    (TYPE_PROJECT, "Project Discussion"),
    (TYPE_MIXED, "Mixed Interview"),
]

# ─── Question Categories ────────────────────────────────────────────────────
CATEGORY_HR = "HR"
CATEGORY_TECHNICAL = "Technical"
CATEGORY_RESUME = "Resume"
CATEGORY_PROJECT = "Project"
CATEGORY_CODING = "Coding"
CATEGORY_BEHAVIORAL = "Behavioral"

# ─── Difficulty Levels ──────────────────────────────────────────────────────
DIFFICULTY_EASY = "Easy"
DIFFICULTY_MEDIUM = "Medium"
DIFFICULTY_HARD = "Hard"

DIFFICULTY_CHOICES = [
    (DIFFICULTY_EASY, "Easy"),
    (DIFFICULTY_MEDIUM, "Medium"),
    (DIFFICULTY_HARD, "Hard"),
]

# ─── Question Count Bounds ──────────────────────────────────────────────────
VALID_QUESTION_COUNTS = [5, 10, 15, 20]
DEFAULT_QUESTION_COUNT = 10
MIN_QUESTION_COUNT = 1
MAX_QUESTION_COUNT = 30

# ─── OpenRouter / OpenAI Config ─────────────────────────────────────────────
DEFAULT_MOCK_MODEL = "meta-llama/llama-3.1-8b-instruct:free"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
MOCK_TIMEOUT_SECONDS = 60
