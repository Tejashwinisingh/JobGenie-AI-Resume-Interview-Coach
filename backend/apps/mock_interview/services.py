"""
apps/mock_interview/services.py

Service layer for Module 9 — AI Mock Interview System.
Orchestrates session lifecycle: Start → Answer Question → Advance → Finish.
Designed to store all Q&A data cleanly for Module 10 (AI Answer Evaluation Engine).
"""
import logging
from typing import Any, Dict, Tuple

from django.utils import timezone

from apps.job_matching.models import JobDescription
from apps.resumes.models import Resume

from .constants import STATUS_COMPLETED, STATUS_IN_PROGRESS
from .models import InterviewQuestion, InterviewSession
from .openai_client import MockInterviewAIClient
from .utils import build_session_context

logger = logging.getLogger(__name__)


class MockInterviewService:
    """
    Orchestrates interactive AI Mock Interview state machine.
    """

    @staticmethod
    def start_session(
        user,
        resume: Resume,
        job_description: JobDescription | None = None,
        role: str = "Python Developer",
        difficulty: str = "Medium",
        interview_type: str = "Mixed",
        question_count: int = 10,
    ) -> Tuple[InterviewSession, InterviewQuestion]:
        """
        Initialize a new mock interview session and generate Question #1.

        Returns:
            Tuple[session, question_1]
        """
        logger.info(
            f"Starting Mock Interview session for user {user.email}: "
            f"role='{role}', difficulty='{difficulty}', type='{interview_type}', count={question_count}"
        )

        session = InterviewSession.objects.create(
            user=user,
            resume=resume,
            job_description=job_description,
            role=role,
            difficulty=difficulty,
            interview_type=interview_type,
            status=STATUS_IN_PROGRESS,
            current_question=1,
            total_questions=question_count,
            completed_questions=0,
        )

        # Build context and generate Q1
        context = build_session_context(session)
        client = MockInterviewAIClient()
        category, question_text = client.generate_next_question(context)

        # Save Q1 to database
        q1 = InterviewQuestion.objects.create(
            session=session,
            question_number=1,
            category=category,
            question=question_text,
        )

        logger.info(f"Session #{session.pk} started. Q1 #{q1.pk} created: [{category}] {question_text[:50]}")
        return session, q1

    @staticmethod
    def submit_answer(
        session: InterviewSession,
        answer_text: str,
    ) -> Dict[str, Any]:
        """
        Submit answer for current question and advance the interview.

        Args:
            session: Active InterviewSession instance.
            answer_text: Candidate's response.

        Returns:
            Dict: {
                "session": session,
                "is_completed": bool,
                "completed_question": previous_q,
                "next_question": next_q or None,
            }
        """
        if session.status == STATUS_COMPLETED:
            raise ValueError("Interview session is already completed.")

        # Find current question
        current_q_num = session.current_question
        try:
            current_q = session.questions.get(question_number=current_q_num)
        except InterviewQuestion.DoesNotExist:
            # Fallback if question record missing
            category, question_text = MockInterviewAIClient().generate_next_question(
                build_session_context(session)
            )
            current_q = InterviewQuestion.objects.create(
                session=session,
                question_number=current_q_num,
                category=category,
                question=question_text,
            )

        # Record candidate answer
        current_q.user_answer = answer_text
        current_q.answered_at = timezone.now()
        current_q.save()

        # Update session completion count
        session.completed_questions += 1

        # Check if interview is finished
        if session.completed_questions >= session.total_questions:
            session.status = STATUS_COMPLETED
            session.completed_at = timezone.now()
            session.save()
            logger.info(f"Session #{session.pk} completed ({session.completed_questions}/{session.total_questions}).")
            return {
                "session": session,
                "is_completed": True,
                "completed_question": current_q,
                "next_question": None,
            }

        # Otherwise, advance to next question
        session.current_question += 1
        session.save()

        # Generate Next Question (Q# = session.current_question)
        context = build_session_context(session)
        client = MockInterviewAIClient()
        category, question_text = client.generate_next_question(context)

        next_q = InterviewQuestion.objects.create(
            session=session,
            question_number=session.current_question,
            category=category,
            question=question_text,
        )

        logger.info(f"Session #{session.pk} advanced to Q{next_q.question_number} [{category}].")
        return {
            "session": session,
            "is_completed": False,
            "completed_question": current_q,
            "next_question": next_q,
        }

    @staticmethod
    def finish_session(session: InterviewSession) -> InterviewSession:
        """
        Manually finish / terminate an interview session early.
        """
        if session.status != STATUS_COMPLETED:
            session.status = STATUS_COMPLETED
            session.completed_at = timezone.now()
            session.save()
            logger.info(f"Session #{session.pk} manually finished.")
        return session
