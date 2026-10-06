"""
apps/ats/evaluators/formatting.py

FormattingEvaluator — Weight: 15 points.

Evaluates the basic formatting and parsability quality of the resume:
  - Text was successfully extracted (non-empty)
  - Minimum content length
  - No signs of corrupted/garbled content
  - Reasonable whitespace ratio
  - Paragraph separation exists
"""
from typing import Dict, Any

from ..constants import WEIGHTS, MIN_TEXT_LENGTH, MAX_WHITESPACE_RATIO
from ..utils import count_words, whitespace_ratio


class FormattingEvaluator:
    """
    Evaluates resume formatting and parsability.

    Responsibility:
        Ensure the resume text was correctly extracted and has
        adequate structure for ATS processing.
    """

    WEIGHT: int = WEIGHTS["formatting"]

    def evaluate(self, cleaned_text: str, raw_text: str) -> Dict[str, Any]:
        """
        Run formatting checks and return a score with details.

        Args:
            cleaned_text: Cleaned resume text from Module 3.
            raw_text: Raw extracted text from Module 3.

        Returns:
            Dict with keys: score, max_score, warnings, details.
        """
        max_score = self.WEIGHT
        score = 0
        warnings = []
        details = {}

        text = cleaned_text or raw_text or ""

        # ── Check 1: Text extraction succeeded (3 points) ─────────────────
        if text.strip():
            score += 3
            details["text_extracted"] = True
        else:
            warnings.append("Resume text could not be extracted or is empty.")
            details["text_extracted"] = False
            return {
                "score": 0,
                "max_score": max_score,
                "warnings": warnings,
                "details": details,
            }

        # ── Check 2: Minimum content length (3 points) ────────────────────
        char_count = len(text.strip())
        details["char_count"] = char_count
        if char_count >= MIN_TEXT_LENGTH:
            score += 3
        else:
            warnings.append(
                f"Resume appears very short ({char_count} characters). "
                "Minimum expected: 100 characters."
            )

        # ── Check 3: Word count is reasonable (3 points) ──────────────────
        word_count = count_words(text)
        details["word_count"] = word_count
        if word_count >= 80:
            score += 3
        elif word_count >= 40:
            score += 2
            warnings.append("Resume has fewer than 80 words. Consider expanding content.")
        else:
            score += 1
            warnings.append("Resume word count is critically low (< 40 words).")

        # ── Check 4: Whitespace ratio check (3 points) ────────────────────
        ws_ratio = whitespace_ratio(text)
        details["whitespace_ratio"] = round(ws_ratio, 3)
        if ws_ratio <= MAX_WHITESPACE_RATIO:
            score += 3
        elif ws_ratio <= 0.55:
            score += 2
            warnings.append("Resume contains excessive whitespace.")
        else:
            score += 1
            warnings.append(
                "Resume has very high whitespace ratio — possible formatting issue."
            )

        # ── Check 5: Paragraph/section breaks exist (3 points) ────────────
        newline_count = text.count("\n")
        details["newline_count"] = newline_count
        if newline_count >= 10:
            score += 3
        elif newline_count >= 4:
            score += 2
            warnings.append("Resume has very few section breaks.")
        else:
            score += 1
            warnings.append(
                "Resume appears to be a single block of text with no section separation."
            )

        return {
            "score": min(score, max_score),
            "max_score": max_score,
            "warnings": warnings,
            "details": details,
        }
