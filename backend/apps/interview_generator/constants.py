"""
apps/interview_generator/constants.py

Constants for the Interview Question Generator module.
"""

# ─── Question Categories ────────────────────────────────────────────────────
CATEGORY_HR = "HR"
CATEGORY_TECHNICAL = "Technical"
CATEGORY_RESUME = "Resume"
CATEGORY_PROJECT = "Project"
CATEGORY_CODING = "Coding"
CATEGORY_BEHAVIORAL = "Behavioral"

ALL_CATEGORIES = [
    CATEGORY_HR,
    CATEGORY_TECHNICAL,
    CATEGORY_RESUME,
    CATEGORY_PROJECT,
    CATEGORY_CODING,
    CATEGORY_BEHAVIORAL,
]

# ─── Difficulty Levels ──────────────────────────────────────────────────────
DIFFICULTY_EASY = "Easy"
DIFFICULTY_MEDIUM = "Medium"
DIFFICULTY_HARD = "Hard"

DIFFICULTY_CHOICES = [
    (DIFFICULTY_EASY, "Easy"),
    (DIFFICULTY_MEDIUM, "Medium"),
    (DIFFICULTY_HARD, "Hard"),
]

# ─── Question Count Options ─────────────────────────────────────────────────
VALID_QUESTION_COUNTS = [5, 10, 20, 30]
DEFAULT_QUESTION_COUNT = 10
MAX_QUESTION_COUNT = 30

# ─── OpenRouter / OpenAI Config ─────────────────────────────────────────────
DEFAULT_INTERVIEW_MODEL = "meta-llama/llama-3.1-8b-instruct:free"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
INTERVIEW_TIMEOUT_SECONDS = 60

# Category distribution by count (approximate split)
CATEGORY_DISTRIBUTION = {
    5:  {"HR": 1, "Technical": 2, "Resume": 1, "Behavioral": 1},
    10: {"HR": 2, "Technical": 3, "Resume": 2, "Project": 1, "Coding": 1, "Behavioral": 1},
    20: {"HR": 3, "Technical": 5, "Resume": 4, "Project": 3, "Coding": 3, "Behavioral": 2},
    30: {"HR": 4, "Technical": 7, "Resume": 6, "Project": 5, "Coding": 4, "Behavioral": 4},
}
