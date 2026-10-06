"""
apps/job_matching/constants.py

Central configuration for the Job Description Matching Engine.
All weights, thresholds, degree equivalencies, and section patterns
are defined here.
"""
from typing import Dict, List, Tuple

# ─── Category Match Weights (Total = 100) ────────────────────────────────────
WEIGHTS: Dict[str, int] = {
    "skills":         50,
    "experience":     20,
    "education":      10,
    "certifications": 10,
    "keywords":       10,
}

# ─── Grade Thresholds ─────────────────────────────────────────────────────────
GRADE_THRESHOLDS: List[Tuple[int, str, str]] = [
    (90, "A+", "Excellent Match"),
    (80, "A",  "Very Good"),
    (70, "B",  "Good Match"),
    (60, "C",  "Average Match"),
    (0,  "D",  "Needs Improvement"),
]

# ─── Degree Hierarchy & Equivalencies ─────────────────────────────────────────
# Higher rank index = higher qualification level.
DEGREE_LEVELS: Dict[str, int] = {
    "phd": 5,
    "doctorate": 5,
    "master": 4,
    "m.tech": 4,
    "mtech": 4,
    "m.s": 4,
    "ms": 4,
    "m.ca": 4,
    "mca": 4,
    "m.sc": 4,
    "msc": 4,
    "mba": 4,
    "bachelor": 3,
    "b.tech": 3,
    "btech": 3,
    "b.e": 3,
    "be": 3,
    "b.sc": 3,
    "bsc": 3,
    "b.ca": 3,
    "bca": 3,
    "b.s": 3,
    "bs": 3,
    "diploma": 2,
    "associate": 2,
    "high school": 1,
}

# Equivalent degree families (used for partial match scoring)
EQUIVALENT_DEGREES: Dict[str, List[str]] = {
    "computer science": ["computer science", "cs", "it", "information technology", "computer engineering", "software engineering"],
    "engineering": ["b.tech", "btech", "b.e", "be", "m.tech", "mtech"],
    "bachelor": ["b.tech", "btech", "b.e", "be", "b.sc", "bsc", "b.ca", "bca", "bachelor"],
    "master": ["m.tech", "mtech", "m.e", "me", "m.sc", "msc", "m.ca", "mca", "ms", "master", "mba"],
}

# ─── Allowed File Extensions ──────────────────────────────────────────────────
ALLOWED_EXTENSIONS: Dict[str, str] = {
    ".pdf": "pdf",
    ".docx": "docx",
}

# Max allowed file size: 5 MB
MAX_FILE_SIZE_BYTES: int = 5 * 1024 * 1024
