"""
apps/interview_evaluation/services.py

Service layer for Module 10 — AI Answer Evaluation & Interview Analysis Engine.
"""
import logging

from apps.mock_interview.models import InterviewSession

from .models import InterviewEvaluation
from .openai_client import InterviewEvaluationAIClient
from .utils import build_evaluation_context

logger = logging.getLogger(__name__)


class InterviewEvaluationService:
    """
    Service layer orchestrating interview session evaluations.
    """

    @staticmethod
    def evaluate_session(session: InterviewSession) -> InterviewEvaluation:
        """
        Evaluate a completed interview session and store results in database.

        Args:
            session: InterviewSession instance.

        Returns:
            InterviewEvaluation model instance.
        """
        logger.info(f"Evaluating InterviewSession #{session.pk} (Role: {session.role}).")

        context = build_evaluation_context(session)
        client = InterviewEvaluationAIClient()
        data = client.evaluate_interview_session(context)

        # Parse & sanitize scores (ensure within 0-100)
        overall_score = max(0, min(100, int(data.get("overall_score", 70))))
        tech_score = max(0, min(100, int(data.get("technical_score", overall_score))))
        comm_score = max(0, min(100, int(data.get("communication_score", overall_score))))
        conf_score = max(0, min(100, int(data.get("confidence_score", overall_score))))
        gram_score = max(0, min(100, int(data.get("grammar_score", overall_score))))
        prob_score = max(0, min(100, int(data.get("problem_solving_score", overall_score))))
        prof_score = max(0, min(100, int(data.get("professionalism_score", overall_score))))

        avg_resp_len = int(data.get("average_response_length", context.get("average_response_length", 0)))
        duration_str = str(data.get("interview_duration", context.get("interview_duration", "0m 0s")))

        recommendation = data.get("hiring_recommendation", "Recommended")
        summary = data.get("summary", "Interview session evaluated successfully.")
        strengths = data.get("strengths", [])
        weaknesses = data.get("weaknesses", [])
        topics = data.get("recommended_topics", [])
        qa_analysis = data.get("question_analysis", [])

        # Create or update evaluation record
        evaluation, created = InterviewEvaluation.objects.update_or_create(
            session=session,
            defaults={
                "overall_score": overall_score,
                "technical_score": tech_score,
                "communication_score": comm_score,
                "confidence_score": conf_score,
                "grammar_score": gram_score,
                "problem_solving_score": prob_score,
                "professionalism_score": prof_score,
                "average_response_length": avg_resp_len,
                "interview_duration": duration_str,
                "hiring_recommendation": recommendation,
                "summary": summary,
                "strengths": strengths,
                "weaknesses": weaknesses,
                "recommended_topics": topics,
                "question_analysis": qa_analysis,
            },
        )

        action = "Created" if created else "Updated"
        logger.info(f"{action} Evaluation #{evaluation.pk} for Session #{session.pk} (Score: {overall_score}/100).")
        return evaluation

    @staticmethod
    def get_evaluation(session: InterviewSession) -> InterviewEvaluation | None:
        """Retrieve existing evaluation for a session or None."""
        return getattr(session, "evaluation", None)
