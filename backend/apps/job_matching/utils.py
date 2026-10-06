"""
apps/job_matching/utils.py

Shared utility functions for text normalization, keyword extraction,
and degree matching.
"""
import re
import string
from typing import List, Set, Tuple

from .constants import DEGREE_LEVELS, EQUIVALENT_DEGREES


def normalize_text(text: str) -> str:
    """
    Lowercase text, remove punctuation, and normalize whitespace.

    Args:
        text: Raw text string.

    Returns:
        Normalized text string.
    """
    if not text:
        return ""
    text = text.lower()
    text = text.translate(str.maketrans(string.punctuation, " " * len(string.punctuation)))
    return re.sub(r"\s+", " ", text).strip()


def extract_keywords_from_text(text: str) -> Set[str]:
    """
    Extract set of normalized words from text, excluding common English stopwords.

    Args:
        text: Raw or cleaned text string.

    Returns:
        Set of clean keyword strings.
    """
    stopwords = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "up", "about", "into", "over", "after",
        "is", "are", "was", "were", "be", "been", "being", "have", "has",
        "had", "do", "does", "did", "will", "would", "should", "can", "could",
        "may", "might", "must", "shall", "this", "that", "these", "those",
        "my", "your", "his", "her", "its", "our", "their", "we", "you", "they",
        "he", "she", "it", "who", "which", "what", "where", "when", "why", "how",
        "all", "any", "both", "each", "few", "more", "most", "other", "some",
        "such", "no", "nor", "not", "only", "own", "same", "so", "than", "too",
        "very", "just", "work", "job", "position", "role", "candidate", "company",
        "team", "responsibilities", "requirements", "qualification", "qualifications",
    }
    normalized = normalize_text(text)
    words = set(normalized.split())
    return {w for w in words if len(w) > 2 and w not in stopwords and not w.isdigit()}


def match_degree_level(req_degree: str, res_degree: str) -> Tuple[str, float]:
    """
    Compare required degree against candidate resume degree.

    Args:
        req_degree: Required degree string from JD (e.g. "B.Tech in Computer Science").
        res_degree: Candidate degree string from resume (e.g. "MCA").

    Returns:
        Tuple of (match_status: str, score_ratio: float)
        match_status can be: "Full Match", "Partial Match", "No Match"
        score_ratio is between 0.0 and 1.0.
    """
    if not req_degree:
        return "Full Match", 1.0
    if not res_degree:
        return "No Match", 0.0

    req_norm = req_degree.lower()
    res_norm = res_degree.lower()

    # Exact string or substring match
    if req_norm in res_norm or res_norm in req_norm:
        return "Full Match", 1.0

    # Determine degree levels
    req_level = 0
    res_level = 0

    for deg, lvl in DEGREE_LEVELS.items():
        if deg in req_norm:
            req_level = max(req_level, lvl)
        if deg in res_norm:
            res_level = max(res_level, lvl)

    # If candidate degree level >= required level
    if req_level > 0 and res_level >= req_level:
        return "Full Match", 1.0
    elif req_level > 0 and res_level == (req_level - 1):
        # Candidate has 1 level lower (e.g. Bachelor when Master required)
        return "Partial Match", 0.6

    # Equivalent degree family check
    for family, aliases in EQUIVALENT_DEGREES.items():
        req_in_family = any(a in req_norm for a in aliases)
        res_in_family = any(a in res_norm for a in aliases)
        if req_in_family and res_in_family:
            return "Partial Match", 0.8

    return "No Match", 0.0


def parse_experience_years(text: str) -> float:
    """
    Extract required years of experience from text string.

    Examples:
        "3+ years experience" -> 3.0
        "5-7 years" -> 5.0
        "1 to 3 yrs" -> 1.0
        "Fresher" / "0 years" -> 0.0

    Args:
        text: Text string mentioning experience.

    Returns:
        Float number of required years.
    """
    if not text:
        return 0.0
    text_lower = text.lower()

    if "fresher" in text_lower or "entry level" in text_lower or "intern" in text_lower:
        return 0.0

    # Patterns like "3+ years", "3-5 years", "3 to 5 years", "3 years"
    patterns = [
        r"(\d+)\s*(?:\+|-\s*\d+|to\s*\d+)?\s*(?:years?|yrs?)",
        r"(\d+)\s*\+\s*(?:years?|yrs?)",
        r"(?:at least|minimum)\s*(\d+)\s*(?:years?|yrs?)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text_lower)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                pass
    return 0.0
