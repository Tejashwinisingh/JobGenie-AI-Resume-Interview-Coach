"""
apps/ats/evaluators/keywords.py

KeywordsEvaluator — Weight: 25 points.

Evaluates technical keyword density and variety in resume text.
- Counts unique valid technical keywords found
- Detects keyword stuffing (penalizes unnatural density)
- Rewards natural occurrences across multiple contexts
"""
import re
from typing import Dict, Any, List, Set

from ..constants import WEIGHTS, ALL_KEYWORDS, KEYWORD_STUFFING_THRESHOLD
from ..utils import count_words


class KeywordsEvaluator:
    """
    Evaluates technical keyword presence and density.

    Responsibility:
        Find all technical keywords in cleaned resume text,
        detect stuffing, and score based on unique keyword count.
    """

    WEIGHT: int = WEIGHTS["keywords"]

    # Keyword count → score thresholds
    SCORE_TIERS: List[tuple] = [
        (30, 25),  # 30+ unique keywords → full score
        (25, 22),
        (20, 20),
        (15, 17),
        (12, 14),
        (9,  11),
        (6,   8),
        (3,   5),
        (1,   3),
        (0,   0),
    ]

    def evaluate(self, cleaned_text: str) -> Dict[str, Any]:
        """
        Scan resume text for technical keywords and compute score.

        Args:
            cleaned_text: Cleaned resume text from Module 3.

        Returns:
            Dict with score, max_score, warnings, details,
                  keywords_found, keyword_count.
        """
        max_score = self.WEIGHT
        warnings: List[str] = []
        text = cleaned_text or ""

        if not text.strip():
            return {
                "score": 0,
                "max_score": max_score,
                "warnings": ["No text content to evaluate keywords."],
                "details": {"keyword_count": 0, "stuffed_keywords": []},
                "keywords_found": [],
                "keyword_count": 0,
            }

        total_words = count_words(text)
        text_lower = text.lower()

        found_keywords: List[str] = []
        stuffed_keywords: List[str] = []
        seen: Set[str] = set()

        for kw in ALL_KEYWORDS:
            kw_lower = kw.lower()
            if kw_lower in seen:
                continue

            # Multi-word vs single-word matching
            escaped = re.escape(kw_lower)
            if " " in kw:
                pattern = escaped
            else:
                pattern = rf"\b{escaped}\b"

            matches = re.findall(pattern, text_lower)
            count = len(matches)

            if count > 0:
                seen.add(kw_lower)
                # Stuffing detection
                if total_words > 0 and (count / total_words) > KEYWORD_STUFFING_THRESHOLD:
                    stuffed_keywords.append(kw)
                    warnings.append(
                        f'Possible keyword stuffing detected for "{kw}" '
                        f"({count} occurrences)."
                    )
                else:
                    found_keywords.append(kw)

        unique_count = len(found_keywords)

        # Determine score from tiers
        score = 0
        for threshold, tier_score in self.SCORE_TIERS:
            if unique_count >= threshold:
                score = tier_score
                break

        if unique_count == 0:
            warnings.append(
                "No recognizable technical keywords detected. "
                "Add relevant technologies from your field."
            )
        elif unique_count < 6:
            warnings.append(
                f"Only {unique_count} technical keyword(s) found. "
                "ATS systems expect at least 8–10 relevant skills."
            )

        return {
            "score": min(score, max_score),
            "max_score": max_score,
            "warnings": warnings,
            "details": {
                "keyword_count": unique_count,
                "stuffed_keywords": stuffed_keywords,
                "total_words": total_words,
            },
            "keywords_found": found_keywords,
            "keyword_count": unique_count,
        }
