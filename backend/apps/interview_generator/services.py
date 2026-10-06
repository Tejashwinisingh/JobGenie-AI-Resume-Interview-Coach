"""
apps/interview_generator/services.py

Service layer for the Interview Question Generator module.
Orchestrates: context building → AI client → model persistence.
Reusable by future modules (AI Mock Interview, AI Answer Evaluator).
"""
import logging
from typing import Any, Dict

from apps.resumes.models import Resume

from .models import InterviewQuestionSet
from .openai_client import InterviewAIClient
from .utils import build_interview_context

logger = logging.getLogger(__name__)


class InterviewGeneratorService:
    """
    Orchestrates interview question generation.

    Usage:
        question_set = InterviewGeneratorService.generate(
            resume=resume_instance,
            job_role="Backend Developer",
            difficulty="Medium",
            count=10,
        )
    """

    @staticmethod
    def generate(
        resume: Resume,
        job_role: str,
        difficulty: str,
        count: int,
    ) -> InterviewQuestionSet:
        """
        Generate a new interview question set for the given resume.

        Steps:
        1. Build context from parsed resume + ATS + job match.
        2. Call AI client (OpenRouter → OpenAI → fallback).
        3. Persist results to InterviewQuestionSet model.
        4. Return saved model instance.

        Args:
            resume: Resume ORM instance.
            job_role: Target role string.
            difficulty: "Easy" | "Medium" | "Hard"
            count: Number of questions.

        Returns:
            Newly created InterviewQuestionSet instance.

        Raises:
            Exception: Only if both AI call and fallback both fail (shouldn't happen).
        """
        logger.info(
            f"Generating {count} {difficulty} interview questions for resume #{resume.pk}, role='{job_role}'"
        )

        # ── 1. Build Context ────────────────────────────────────────────────
        context: Dict[str, Any] = build_interview_context(
            resume=resume,
            job_role=job_role,
            difficulty=difficulty,
            count=count,
        )

        # ── 2. Call AI Client ───────────────────────────────────────────────
        client = InterviewAIClient()
        result: Dict[str, Any] = client.generate_questions(context)

        # ── 3. Validate Result ──────────────────────────────────────────────
        questions = result.get("questions", [])
        if not questions:
            logger.warning("AI client returned 0 questions. Running fallback.")
            from .utils import generate_fallback_questions
            result = generate_fallback_questions(context)
            questions = result.get("questions", [])

        # ── 4. Persist to Database ──────────────────────────────────────────
        question_set = InterviewQuestionSet.objects.create(
            resume=resume,
            job_role=job_role,
            difficulty=difficulty,
            question_count=len(questions),
            questions=questions,
            provider=client.provider,
        )

        logger.info(
            f"Saved InterviewQuestionSet #{question_set.pk} with {len(questions)} questions "
            f"via {client.provider}."
        )
        return question_set

    @staticmethod
    def get_latest(resume: Resume) -> InterviewQuestionSet | None:
        """
        Retrieve the most recent question set for a resume.

        Args:
            resume: Resume ORM instance.

        Returns:
            Latest InterviewQuestionSet or None.
        """
        return (
            resume.interview_question_sets
            .order_by("-created_at")
            .first()
        )

    @staticmethod
    def get_all(resume: Resume):
        """
        Retrieve all question sets for a resume, newest first.

        Args:
            resume: Resume ORM instance.

        Returns:
            QuerySet of InterviewQuestionSet.
        """
        return resume.interview_question_sets.order_by("-created_at")
