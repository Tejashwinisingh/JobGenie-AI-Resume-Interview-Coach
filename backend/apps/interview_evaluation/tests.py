"""
apps/interview_evaluation/tests.py

Unit tests and API test suite for Module 10 — AI Answer Evaluation & Interview Analysis Engine.
"""
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.mock_interview.constants import STATUS_COMPLETED, STATUS_IN_PROGRESS
from apps.mock_interview.models import InterviewQuestion, InterviewSession
from apps.resumes.models import Resume

from .constants import (
    REC_HIGHLY_RECOMMENDED,
    REC_NOT_RECOMMENDED,
    REC_RECOMMENDED,
)
from .models import InterviewEvaluation
from .services import InterviewEvaluationService
from .utils import build_evaluation_context, generate_fallback_evaluation

User = get_user_model()


def make_pdf_content() -> bytes:
    return b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF\n"


def create_user_and_token(email: str = "evaluser@example.com", password: str = "EvalPass123!"):
    user = User.objects.create_user(
        email=email,
        password=password,
        full_name="Eval Tester",
    )
    refresh = RefreshToken.for_user(user)
    return user, str(refresh.access_token)


def create_completed_session(user, role: str = "Python Developer", question_count: int = 2):
    resume = Resume.objects.create(
        user=user,
        original_filename="sample_resume.pdf",
        file_size=1024,
        file_type=Resume.FILE_TYPE_PDF,
    )
    resume.file.save("sample_resume.pdf", ContentFile(make_pdf_content()), save=True)

    session = InterviewSession.objects.create(
        user=user,
        resume=resume,
        role=role,
        difficulty="Medium",
        interview_type="Mixed",
        status=STATUS_COMPLETED,
        current_question=question_count,
        total_questions=question_count,
        completed_questions=question_count,
    )

    # Q1
    InterviewQuestion.objects.create(
        session=session,
        question_number=1,
        category="HR",
        question="Tell me about yourself.",
        user_answer="I am a Python Developer with 3 years of experience in Django and PostgreSQL.",
    )

    # Q2
    if question_count >= 2:
        InterviewQuestion.objects.create(
            session=session,
            question_number=2,
            category="Technical",
            question="Explain Django Middleware.",
            user_answer="Django Middleware is a plugin framework for light, low-level hooks to globally alter Django input or output.",
        )

    return session


# ─── Unit Tests: Utils & Fallback ───────────────────────────────────────────

class InterviewEvaluationUtilsTestCase(TestCase):

    def setUp(self):
        self.user, _ = create_user_and_token("utils_eval@example.com")
        self.session = create_completed_session(self.user)

    def test_build_evaluation_context(self):
        ctx = build_evaluation_context(self.session)
        self.assertEqual(ctx["job_role"], "Python Developer")
        self.assertIn("Tell me about yourself.", ctx["transcript"])

    def test_generate_fallback_evaluation(self):
        ctx = build_evaluation_context(self.session)
        res = generate_fallback_evaluation(ctx)
        self.assertIn("overall_score", res)
        self.assertGreater(res["overall_score"], 0)
        self.assertIn("question_analysis", res)
        self.assertEqual(len(res["question_analysis"]), 2)


# ─── Unit Tests: Service Layer ─────────────────────────────────────────────

class InterviewEvaluationServiceTestCase(TestCase):

    def setUp(self):
        self.user, _ = create_user_and_token("service_eval@example.com")
        self.session = create_completed_session(self.user)

    def test_evaluate_session_creates_evaluation_record(self):
        eval_obj = InterviewEvaluationService.evaluate_session(self.session)
        self.assertIsInstance(eval_obj, InterviewEvaluation)
        self.assertEqual(eval_obj.session, self.session)
        self.assertGreater(eval_obj.overall_score, 0)
        self.assertIn(eval_obj.hiring_recommendation, [REC_HIGHLY_RECOMMENDED, REC_RECOMMENDED, REC_NOT_RECOMMENDED])
        self.assertGreater(len(eval_obj.question_analysis), 0)

    def test_get_evaluation_returns_existing(self):
        eval_obj = InterviewEvaluationService.evaluate_session(self.session)
        retrieved = InterviewEvaluationService.get_evaluation(self.session)
        self.assertEqual(eval_obj.pk, retrieved.pk)


# ─── API Tests ──────────────────────────────────────────────────────────────

class InterviewEvaluationAPITestCase(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user, self.token = create_user_and_token()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")
        self.session = create_completed_session(self.user)

    def test_evaluate_session_api_success(self):
        res = self.client.post(f"/api/interviews/{self.session.id}/evaluate/", format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        data = res.json()
        self.assertEqual(data["session_id"], self.session.id)
        self.assertIn("overall_score", data)
        self.assertIn("hiring_recommendation", data)
        self.assertIn("question_analysis", data)

    def test_get_evaluation_api_success(self):
        # Create evaluation first
        self.client.post(f"/api/interviews/{self.session.id}/evaluate/", format="json")

        # GET evaluation
        res = self.client.get(f"/api/interviews/{self.session.id}/evaluation/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        data = res.json()
        self.assertEqual(data["session_id"], self.session.id)

    def test_evaluate_uncompleted_session_fails(self):
        in_progress_session = InterviewSession.objects.create(
            user=self.user,
            resume=self.session.resume,
            role="DevOps Engineer",
            status=STATUS_IN_PROGRESS,
            completed_questions=0,
            total_questions=10,
        )
        res = self.client.post(f"/api/interviews/{in_progress_session.id}/evaluate/", format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_nonexistent_evaluation_returns_404(self):
        res = self.client.get(f"/api/interviews/{self.session.id}/evaluation/")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_evaluate_nonexistent_session_returns_404(self):
        res = self.client.post("/api/interviews/99999/evaluate/", format="json")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthorized_access_denied(self):
        unauth_client = APIClient()
        res = unauth_client.post(f"/api/interviews/{self.session.id}/evaluate/", format="json")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_evaluation_with_empty_answers(self):
        session = create_completed_session(self.user, role="React Developer", question_count=1)
        q = session.questions.first()
        q.user_answer = ""
        q.save()

        res = self.client.post(f"/api/interviews/{session.id}/evaluate/", format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        data = res.json()
        self.assertIn("question_analysis", data)
        self.assertEqual(data["question_analysis"][0]["technical"], 0)

    def test_evaluation_with_short_answers(self):
        session = create_completed_session(self.user, role="Data Engineer", question_count=1)
        q = session.questions.first()
        q.user_answer = "Yes I know SQL."
        q.save()

        res = self.client.post(f"/api/interviews/{session.id}/evaluate/", format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        data = res.json()
        self.assertLessEqual(data["question_analysis"][0]["technical"], 5)

    def test_evaluation_with_long_answers(self):
        session = create_completed_session(self.user, role="System Architect", question_count=1)
        q = session.questions.first()
        q.user_answer = (
            "I design microservice architectures using Domain Driven Design principles. "
            "We decouple services via Kafka event streaming, maintain PostgreSQL databases per domain, "
            "and implement Redis distributed locks for cache consistency and high concurrency."
        )
        q.save()

        res = self.client.post(f"/api/interviews/{session.id}/evaluate/", format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        data = res.json()
        self.assertGreaterEqual(data["question_analysis"][0]["technical"], 8)
        self.assertGreater(data["average_response_length"], 20)
        self.assertIn("interview_duration", data)

