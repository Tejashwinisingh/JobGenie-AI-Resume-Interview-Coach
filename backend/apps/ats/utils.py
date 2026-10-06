"""
apps/ats/utils.py

Shared utility functions for the ATS evaluation engine.
All functions are pure / stateless and independently testable.
"""
import re
import string
from typing import List, Tuple


def normalize_text(text: str) -> str:
    """
    Lowercase and strip punctuation from text for keyword matching.

    Args:
        text: Raw text string.

    Returns:
        Normalized text with lowercase and no punctuation.
    """
    if not text:
        return ""
    text = text.lower()
    # Replace punctuation with space to avoid joining words
    text = text.translate(str.maketrans(string.punctuation, " " * len(string.punctuation)))
    # Collapse multiple spaces
    text = re.sub(r"\s+", " ", text).strip()
    return text


def find_section_in_text(section_aliases: List[str], text: str) -> Tuple[bool, str]:
    """
    Check if any alias for a section heading exists in the text.

    A heading is recognized if the alias appears on its own line or
    is followed by a newline/colon (typical resume formatting).

    Args:
        section_aliases: List of acceptable heading variants.
        text: Cleaned resume text.

    Returns:
        Tuple (found: bool, matched_alias: str)
    """
    if not text:
        return False, ""

    normalized = text.lower()
    for alias in section_aliases:
        alias_lower = alias.lower()
        # Pattern: heading starts a line, optionally followed by : or newline
        pattern = rf"(?:^|\n)\s*{re.escape(alias_lower)}\s*[:\n]"
        if re.search(pattern, normalized):
            return True, alias
        # Fallback: heading appears anywhere as a standalone word group
        word_pattern = rf"\b{re.escape(alias_lower)}\b"
        if re.search(word_pattern, normalized):
            return True, alias
    return False, ""


def count_keyword_occurrences(keyword: str, text: str) -> int:
    """
    Count how many times a keyword appears in text using word boundaries.

    Multi-word keywords (e.g. "spring boot") are matched as phrases.

    Args:
        keyword: The technical keyword to search for.
        text: Normalized resume text.

    Returns:
        Integer count of occurrences.
    """
    if not text or not keyword:
        return 0
    # Use word boundary for single words; phrase match for multi-word
    escaped = re.escape(keyword.lower())
    if " " in keyword:
        pattern = escaped
    else:
        pattern = rf"\b{escaped}\b"
    return len(re.findall(pattern, text.lower()))


def extract_years_from_text(text: str) -> List[int]:
    """
    Extract 4-digit year values from text (1970–2099 range).

    Args:
        text: Any text string.

    Returns:
        List of detected years as integers.
    """
    if not text:
        return []
    matches = re.findall(r"\b(19[7-9]\d|20[0-9]\d)\b", text)
    return [int(m) for m in matches]


def count_words(text: str) -> int:
    """Return the number of whitespace-separated words in text."""
    if not text:
        return 0
    return len(text.split())


def whitespace_ratio(text: str) -> float:
    """
    Compute the fraction of whitespace characters in text.

    Args:
        text: Raw text string.

    Returns:
        Float between 0.0 and 1.0.
    """
    if not text:
        return 1.0
    total = len(text)
    spaces = sum(1 for c in text if c in (" ", "\n", "\t", "\r"))
    return spaces / total
