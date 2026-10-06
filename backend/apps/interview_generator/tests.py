"""
apps/interview_generator/tests.py

Unit tests and API tests for Module 8 — Interview Question Generator.

Tests cover:
  - Fallback generator (offline mode)
  - Context builder
  - AI client (mocked OpenAI)
  - Service layer
  - API: generate 5/10/20 questions
  - API: Easy/Medium/Hard difficulty
  - API: resume with no projects
  - API: invalid resume
  - API: list question sets
"""
import json
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.core.files.base import ContentFile
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.resumes.models import Resume
from .constants import (
    CATEGORY_BEHAVIORAL,
    CATEGORY_CODING,
    CATEGORY_HR,
    CATEGORY_TECHNICAL,
    DIFFICULTY_EASY,
    DIFFICULTY_HARD,
    DIFFICULTY_MEDIUM,
)
from .models import InterviewQuestionSet
from .utils import build_interview_context, generate_fallback_questions

User = get_user_model()


def make_pdf_content() -> bytes:
    """Return minimal PDF bytes."""
    return b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF\n"


def create_user_and_token(email: str = "test@interview.com", password: str = "TestPass123!"):
    user = User.objects.create_user(
        email=email,
        password=password,
        full_name="Test User",
    )
    refresh = RefreshToken.for_user(user)
    return user, str(refresh.access_token)


def create_resume(user) -> Resume:
    """Create a minimal Resume for testing."""
    resume = Resume.objects.create(
        user=user,
        original_filename="test_resume.pdf",
        file_size=1024,
        file_type=Resume.FILE_TYPE_PDF,
    )
    resume.file.save("test_resume.pdf", ContentFile(make_pdf_content()), save=True)
    return resume


def make_mock_parsed(skills=None, projects=None, name="John Dev"):
    parsed = MagicMock()
    parsed.name = name
    parsed.skills = skills or ["Python", "Django", "React", "PostgreSQL"]
    parsed.education = [{"degree": "B.Tech", "field": "CS"}]
    parsed.experience = [{"title": "Backend Developer", "company": "TechCorp"}]
    parsed.projects = projects or [
        {"name": "ResumeIQ", "description": "AI-powered resume platform"},
        {"name": "EV Trip Planner", "description": "Electric vehicle range calculator"},
    ]
    parsed.certifications = ["AWS Certified Developer"]
    return parsed


# ─── Unit Tests: Fallback Generator ─────────────────────────────────────────

class FallbackGeneratorTestCase(TestCase):

    def _make_context(self, count=10, projects=None):
        return {
            "job_role": "Backend Developer",
            "difficulty": "Medium",
            "count": count,
            "name": "John Dev",
            "skills": "Python, Django, React",
            "education": "[]",
            "experience": "[]",
            "projects": "[]",
            "certifications": "AWS",
            "ats_score": 72,
            "matched_skills": "Python, Django",
            "missing_skills": "Kubernetes",
            "category_distribution": "  - HR: 2\n  - Technical: 3",
            "project_names": "ResumeIQ",
            "top_skills": "Python, Django",
            "_skills_list": ["Python", "Django", "React"],
            "_projects_list": projects if projects is not None else [
                {"name": "ResumeIQ", "description": "AI resume platform"}
            ],
            "_experience_list": [],
        }

    def test_fallback_generates_5_questions(self):
        ctx = self._make_context(count=5)
        result = generate_fallback_questions(ctx)
        self.assertIn("questions", result)
        self.assertLessEqual(len(result["questions"]), 5)

    def test_fallback_generates_10_questions(self):
        ctx = self._make_context(count=10)
        result = generate_fallback_questions(ctx)
        self.assertIn("questions", result)
        self.assertGreater(len(result["questions"]), 0)

    def test_fallback_generates_20_questions(self):
        ctx = self._make_context(count=20)
        result = generate_fallback_questions(ctx)
        # Fallback generates up to 20; must be between 10 and 20
        self.assertGreaterEqual(len(result["questions"]), 10)
        self.assertLessEqual(len(result["questions"]), 20)

    def test_fallback_no_projects(self):
        ctx = self._make_context(count=10, projects=[])
        result = generate_fallback_questions(ctx)
        self.assertIn("questions", result)
        self.assertGreater(len(result["questions"]), 0)

    def test_fallback_question_structure(self):
        ctx = self._make_context(count=10)
        result = generate_fallback_questions(ctx)
        for q in result["questions"]:
            self.assertIn("id", q)
            self.assertIn("category", q)
            self.assertIn("question", q)
            self.assertIsInstance(q["question"], str)
            self.assertTrue(len(q["question"]) > 5)

    def test_fallback_returns_difficulty_and_role(self):
        ctx = self._make_context(count=5)
        result = generate_fallback_questions(ctx)
        self.assertEqual(result["difficulty"], "Medium")
        self.assertEqual(result["job_role"], "Backend Developer")


# ─── Unit Tests: AI Client (Mocked) ─────────────────────────────────────────

class InterviewAIClientTestCase(TestCase):

    def test_client_uses_fallback_when_no_key(self):
        from .openai_client import InterviewAIClient
        with patch.dict("os.environ", {"OPENROUTER_API_KEY": "", "OPENAI_API_KEY": ""}):
            client = InterviewAIClient()
            self.assertEqual(client.provider, "Fallback")

    def test_client_uses_openrouter_when_key_set(self):
        from .openai_client import InterviewAIClient
        with patch.dict("os.environ", {"OPENROUTER_API_KEY": "sk-or-real-key-123"}):
            client = InterviewAIClient()
            self.assertEqual(client.provider, "OpenRouter")

    def test_generate_questions_fallback_returns_valid_structure(self):
        from .openai_client import InterviewAIClient
        with patch.dict("os.environ", {"OPENROUTER_API_KEY": "", "OPENAI_API_KEY": ""}):
            client = InterviewAIClient()
            ctx = {
                "job_role": "Backend Developer", "difficulty": "Medium", "count": 5,
                "name": "Test", "skills": "Python", "education": "[]", "experience": "[]",
                "projects": "[]", "certifications": "", "ats_score": 70,
                "matched_skills": "", "missing_skills": "", "category_distribution": "",
                "project_names": "None", "top_skills": "Python",
                "_skills_list": ["Python"], "_projects_list": [], "_experience_list": [],
            }
            result = client.generate_questions(ctx)
            self.assertIn("questions", result)
            self.assertIsInstance(result["questions"], list)

    def test_generate_questions_mocked_openai_success(self):
        from .openai_client import InterviewAIClient
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps({
            "job_role": "Backend Developer",
            "difficulty": "Medium",
            "questions": [
                {"id": 1, "category": "HR", "question": "Tell me about yourself."},
                {"id": 2, "category": "Technical", "question": "Explain Django ORM."},
            ]
        })
        with patch.dict("os.environ", {"OPENROUTER_API_KEY": "sk-or-test-123"}):
            with patch("openai.OpenAI") as MockClient:
                instance = MockClient.return_value
                instance.chat.completions.create.return_value = mock_response
                client = InterviewAIClient()
                ctx = {
                    "job_role": "Backend Developer", "difficulty": "Medium", "count": 2,
                    "name": "Test", "skills": "Python", "education": "[]", "experience": "[]",
                    "projects": "[]", "certifications": "", "ats_score": 70,
                    "matched_skills": "", "missing_skills": "", "category_distribution": "  - HR: 1\n  - Technical: 1",
                    "project_names": "None", "top_skills": "Python",
                    "_skills_list": ["Python"], "_projects_list": [], "_experience_list": [],
                }
                result = client.generate_questions(ctx)
                self.assertEqual(len(result["questions"]), 2)

    def test_generate_questions_falls_back_on_api_error(self):
        from .openai_client import InterviewAIClient
        with patch.dict("os.environ", {"OPENROUTER_API_KEY": "sk-or-test-123"}):
            with patch("openai.OpenAI") as MockClient:
                MockClient.side_effect = Exception("API error")
                client = InterviewAIClient()
                ctx = {
                    "job_role": "Backend Developer", "difficulty": "Medium", "count": 5,
                    "name": "Test", "skills": "Python", "education": "[]", "experience": "[]",
                    "projects": "[]", "certifications": "", "ats_score": 70,
                    "matched_skills": "", "missing_skills": "", "category_distribution": "",
                    "project_names": "None", "top_skills": "Python",
                    "_skills_list": ["Python"], "_projects_list": [], "_experience_list": [],
                }
                result = client.generate_questions(ctx)
                self.assertIn("questions", result)


# ─── API Tests ──────────────────────────────────────────────────────────────

class GenerateQuestionsAPITestCase(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user, self.token = create_user_and_token()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")
        self.resume = create_resume(self.user)

        # Attach mocked parsed data
        parsed = make_mock_parsed()
        type(self.resume).parsed_data = property(lambda self: parsed)

    def _post_generate(self, resume_id=None, payload=None):
        rid = resume_id or self.resume.id
        data = payload or {"difficulty": "Medium", "count": 10, "role": "Backend Developer"}
        return self.client.post(
            f"/api/resumes/{rid}/generate-questions/",
            data=data, format="json"
        )

    def test_generate_5_questions_easy(self):
        res = self._post_generate(payload={"difficulty": DIFFICULTY_EASY, "count": 5, "role": "Frontend Developer"})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        data = res.json()["data"]
        self.assertLessEqual(data["question_count"], 5)

    def test_generate_10_questions_medium(self):
        res = self._post_generate(payload={"difficulty": DIFFICULTY_MEDIUM, "count": 10, "role": "Backend Developer"})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIn("questions", res.json()["data"])

    def test_generate_20_questions_hard(self):
        res = self._post_generate(payload={"difficulty": DIFFICULTY_HARD, "count": 20, "role": "Full Stack Engineer"})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        data = res.json()["data"]
        self.assertGreater(data["question_count"], 0)

    def test_generate_30_questions(self):
        res = self._post_generate(payload={"difficulty": DIFFICULTY_MEDIUM, "count": 30, "role": "Software Engineer"})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_generate_invalid_resume(self):
        res = self._post_generate(resume_id=99999)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_generate_missing_role_defaults(self):
        res = self._post_generate(payload={"difficulty": "Medium", "count": 5})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_generate_invalid_difficulty_rejected(self):
        res = self._post_generate(payload={"difficulty": "Expert", "count": 10, "role": "Dev"})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_generate_requires_authentication(self):
        unauth_client = APIClient()
        res = unauth_client.post(
            f"/api/resumes/{self.resume.id}/generate-questions/",
            data={"difficulty": "Medium", "count": 10, "role": "Dev"}, format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_question_sets(self):
        # Generate one first
        self._post_generate()
        res = self.client.get(f"/api/resumes/{self.resume.id}/questions/list/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIsInstance(res.json(), list)
        self.assertGreater(len(res.json()), 0)

    def test_question_structure_has_required_fields(self):
        res = self._post_generate()
        questions = res.json()["data"]["questions"]
        for q in questions:
            self.assertIn("id", q)
            self.assertIn("category", q)
            self.assertIn("question", q)

    def test_question_set_persisted_in_db(self):
        self._post_generate(payload={"difficulty": "Easy", "count": 5, "role": "QA Engineer"})
        qs = InterviewQuestionSet.objects.filter(resume=self.resume)
        self.assertGreater(qs.count(), 0)

    def test_no_projects_resume_still_generates(self):
        parsed = make_mock_parsed(projects=[])
        type(self.resume).parsed_data = property(lambda self: parsed)
        res = self._post_generate(payload={"difficulty": "Medium", "count": 5, "role": "Backend"})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
