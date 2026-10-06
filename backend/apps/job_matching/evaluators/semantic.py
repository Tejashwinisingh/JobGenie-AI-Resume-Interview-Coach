"""
apps/job_matching/evaluators/semantic.py

SemanticEvaluator — Pure text & role similarity helper.

Calculates semantic token overlap ratio and phrase similarity.
"""
from difflib import SequenceMatcher
from typing import Set

from ..utils import normalize_text


class SemanticEvaluator:
    """
    Computes text and phrase similarity ratios.
    """

    @staticmethod
    def compute_similarity(text1: str, text2: str) -> float:
        """
        Compute sequence matcher similarity ratio between two strings (0.0 to 1.0).
        """
        if not text1 or not text2:
            return 0.0
        n1 = normalize_text(text1)
        n2 = normalize_text(text2)
        return SequenceMatcher(None, n1, n2).ratio()

    @staticmethod
    def compute_jaccard_overlap(text1: str, text2: str) -> float:
        """
        Compute Jaccard token overlap ratio between two texts (0.0 to 1.0).
        """
        tokens1: Set[str] = set(normalize_text(text1).split())
        tokens2: Set[str] = set(normalize_text(text2).split())
        if not tokens1 or not tokens2:
            return 0.0
        intersection = tokens1 & tokens2
        union = tokens1 | tokens2
        return len(intersection) / len(union)
