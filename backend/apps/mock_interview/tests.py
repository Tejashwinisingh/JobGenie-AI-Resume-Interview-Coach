"""
apps/mock_interview/tests.py

Unit tests and API test suite for Module 9 — AI Mock Interview System.
"""
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.job_matching.models import JobDescription
from apps.resumes.models import Resume

from .constants import (
    DIFFICULTY_EASY,
    DIFFICULTY_HARD,
    DIFFICULTY_MEDIUM,
    STATUS_COMPLETED,
    STATUS_IN_PROGRESS,
    TYPE_HR,
    TYPE_MIXED,
    TYPE_TECHNICAL,
)
from .models import InterviewQuestion, InterviewSession
from .services import MockInterviewService
from .utils import build_session_context, generate_fallback_question

User = get_user_model()


def make_pdf_content() -> bytes:
    return b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF\n"


def create_user_and_token(email: str = "mockuser@example.com", password: str = "MockPass123!"):
    user = User.objects.create_user(
        email=email,
        password=password,
        full_name="Mock Tester",
    )
    refresh = RefreshToken.for_user(user)
    return user, str(refresh.access_token)


def create_resume(user) -> Resume:
    resume = Resume.objects.create(
        user=user,
        original_filename="sample_resume.pdf",
        file_size=1024,
        file_type=Resume.FILE_TYPE_PDF,
    )
    resume.file.save("sample_resume.pdf", ContentFile(make_pdf_content()), save=True)
    return resume


def create_jd(user) -> JobDescription:
    return JobDescription.objects.create(
        user=user,
        title="Python Backend Engineer",
        company="Tech Inc",
        raw_text="We need Python, Django, React, Docker, and PostgreSQL developer.",
        cleaned_text="Python Django React Docker PostgreSQL",
    )


# ─── Unit Tests: Utils & Fallback ───────────────────────────────────────────

class MockInterviewUtilsTestCase(TestCase):

    def setUp(self):
        self.user, _ = create_user_and_token("utils_test@example.com")
        self.resume = create_resume(self.user)
        self.session = InterviewSession.objects.create(
            user=self.user,
            resume=self.resume,
            role="Python Developer",
            difficulty="Medium",
            interview_type="Mixed",
            total_questions=5,
        )

    def test_build_session_context(self):
        ctx = build_session_context(self.session)
        self.assertEqual(ctx["job_role"], "Python Developer")
        self.assertEqual(ctx["difficulty"], "Medium")
        self.assertEqual(ctx["total_questions"], 5)

    def test_generate_fallback_question(self):
        ctx = build_session_context(self.session)
        cat, q_text = generate_fallback_question(ctx)
        self.assertIsInstance(cat, str)
        self.assertIsInstance(q_text, str)
        self.assertGreater(len(q_text), 10)


# ─── Unit Tests: Service Layer ─────────────────────────────────────────────

class MockInterviewServiceTestCase(TestCase):

    def setUp(self):
        self.user, _ = create_user_and_token("service_test@example.com")
        self.resume = create_resume(self.user)
        self.jd = create_jd(self.user)

    def test_start_session_creates_session_and_q1(self):
        session, q1 = MockInterviewService.start_session(
            user=self.user,
            resume=self.resume,
            job_description=self.jd,
            role="Django Developer",
            difficulty="Hard",
            interview_type="Technical",
            question_count=5,
        )
        self.assertEqual(session.status, STATUS_IN_PROGRESS)
        self.assertEqual(session.current_question, 1)
        self.assertEqual(session.completed_questions, 0)
        self.assertEqual(q1.question_number, 1)
        self.assertIsNotNone(q1.question)

    def test_submit_answer_advances_to_q2(self):
        session, q1 = MockInterviewService.start_session(
            user=self.user,
            resume=self.resume,
            role="Python Developer",
            question_count=3,
        )
        res = MockInterviewService.submit_answer(session, "I have 3 years of Python experience.")
        self.assertFalse(res["is_completed"])
        self.assertEqual(res["session"].completed_questions, 1)
        self.assertEqual(res["session"].current_question, 2)
        self.assertEqual(res["next_question"].question_number, 2)

    def test_submit_answers_until_completion(self):
        session, _ = MockInterviewService.start_session(
            user=self.user,
            resume=self.resume,
            role="React Developer",
            question_count=2,
        )
        # Answer Q1
        res1 = MockInterviewService.submit_answer(session, "Answer 1")
        self.assertFalse(res1["is_completed"])

        # Answer Q2 (final)
        res2 = MockInterviewService.submit_answer(session, "Answer 2")
        self.assertTrue(res2["is_completed"])
        self.assertEqual(res2["session"].status, STATUS_COMPLETED)
        self.assertEqual(res2["session"].completed_questions, 2)

    def test_finish_session_early(self):
        session, _ = MockInterviewService.start_session(
            user=self.user,
            resume=self.resume,
            question_count=10,
        )
        finished = MockInterviewService.finish_session(session)
        self.assertEqual(finished.status, STATUS_COMPLETED)
        self.assertIsNotNone(finished.completed_at)


# ─── API Tests ──────────────────────────────────────────────────────────────

class MockInterviewAPITestCase(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user, self.token = create_user_and_token()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")
        self.resume = create_resume(self.user)
        self.jd = create_jd(self.user)

    def test_start_interview_api_success(self):
        payload = {
            "resume_id": self.resume.id,
            "job_description_id": self.jd.id,
            "role": "Python Developer",
            "difficulty": "Medium",
            "interview_type": "Mixed",
            "question_count": 5,
        }
        res = self.client.post("/api/interviews/start/", data=payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIn("session_id", res.json())
        self.assertEqual(res.json()["question_number"], 1)
        self.assertIn("question", res.json())

    def test_start_interview_resume_not_found(self):
        payload = {
            "resume_id": 99999,
            "role": "Python Developer",
        }
        res = self.client.post("/api/interviews/start/", data=payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_start_interview_jd_not_found(self):
        payload = {
            "resume_id": self.resume.id,
            "job_description_id": 99999,
            "role": "Python Developer",
        }
        res = self.client.post("/api/interviews/start/", data=payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_submit_answer_api_flow(self):
        # 1. Start interview
        start_res = self.client.post("/api/interviews/start/", data={
            "resume_id": self.resume.id,
            "role": "Backend Engineer",
            "question_count": 2,
        }, format="json")
        sid = start_res.json()["session_id"]

        # 2. Answer Q1
        ans_res = self.client.post(f"/api/interviews/{sid}/answer/", data={
            "answer": "My name is Mock Tester and I specialize in Django REST Framework."
        }, format="json")
        self.assertEqual(ans_res.status_code, status.HTTP_200_OK)
        self.assertFalse(ans_res.json()["is_completed"])
        self.assertEqual(ans_res.json()["question_number"], 2)

        # 3. Answer Q2 (final)
        ans_res2 = self.client.post(f"/api/interviews/{sid}/answer/", data={
            "answer": "Django ORM translates Python code into optimized SQL queries."
        }, format="json")
        self.assertEqual(ans_res2.status_code, status.HTTP_200_OK)
        self.assertTrue(ans_res2.json()["is_completed"])
        self.assertEqual(ans_res2.json()["status"], "Completed")

    def test_submit_empty_answer_rejected(self):
        start_res = self.client.post("/api/interviews/start/", data={
            "resume_id": self.resume.id,
        }, format="json")
        sid = start_res.json()["session_id"]

        res = self.client.post(f"/api/interviews/{sid}/answer/", data={"answer": "   "}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_submit_answer_already_completed(self):
        start_res = self.client.post("/api/interviews/start/", data={
            "resume_id": self.resume.id,
            "question_count": 1,
        }, format="json")
        sid = start_res.json()["session_id"]

        # Complete it
        self.client.post(f"/api/interviews/{sid}/answer/", data={"answer": "Done"}, format="json")

        # Try answering again
        res = self.client.post(f"/api/interviews/{sid}/answer/", data={"answer": "Extra answer"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_session_progress_api(self):
        start_res = self.client.post("/api/interviews/start/", data={
            "resume_id": self.resume.id,
            "question_count": 5,
        }, format="json")
        sid = start_res.json()["session_id"]

        # Answer 1
        self.client.post(f"/api/interviews/{sid}/answer/", data={"answer": "Answer 1"}, format="json")

        # GET Session
        res = self.client.get(f"/api/interviews/{sid}/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        data = res.json()
        self.assertEqual(data["completed_questions"], 1)
        self.assertEqual(data["total_questions"], 5)
        self.assertEqual(data["remaining_questions"], 4)
        self.assertEqual(data["progress"], 20)
        self.assertEqual(len(data["questions"]), 2) # Q1 answered + Q2 active

    def test_finish_interview_api(self):
        start_res = self.client.post("/api/interviews/start/", data={
            "resume_id": self.resume.id,
            "question_count": 10,
        }, format="json")
        sid = start_res.json()["session_id"]

        res = self.client.post(f"/api/interviews/{sid}/finish/", format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.json()["status"], "Completed")

    def test_list_interviews_api(self):
        self.client.post("/api/interviews/start/", data={"resume_id": self.resume.id}, format="json")
        res = self.client.get("/api/interviews/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIsInstance(res.json(), list)
        self.assertGreater(len(res.json()), 0)

    def test_unauthorized_user_access_denied(self):
        unauth_client = APIClient()
        res = unauth_client.post("/api/interviews/start/", data={"resume_id": self.resume.id}, format="json")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
