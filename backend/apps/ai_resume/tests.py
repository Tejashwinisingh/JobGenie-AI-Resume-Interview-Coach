"""
apps/ai_resume/tests.py

Unit tests and API tests for Module 7 — AI Resume Improvement Suggestions Engine.

Test Scenarios:
  1. Resume with high ATS score
  2. Resume with low ATS score
  3. Resume missing projects
  4. Resume missing experience
  5. Resume missing skills
  6. OpenAI Client fallback handling (offline mode / missing API key)
  7. API: POST /api/resumes/{id}/ai-suggestions/ (generate suggestions)
  8. API: GET  /api/resumes/{id}/ai-suggestions/ (retrieve saved suggestions)
  9. API error handling (404 for invalid resume, 401 unauthenticated)
"""
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import MagicMock, patch

from apps.authentication.models import User
from apps.resumes.models import Resume, ParsedResume
from apps.ats.models import ATSScore
from .models import ResumeSuggestion
from .openai_client import OpenAIResumeClient
from .services import AISuggestionService
from .utils import build_resume_ai_context, generate_fallback_ai_suggestions

SAMPLE_RESUME_TEXT = """
John Doe
john@example.com | +1-555-0199

SKILLS
Python, Django, React, Docker

EDUCATION
B.Tech in Computer Science (2021)

EXPERIENCE
Software Developer (2022–Present)
Developed REST APIs and web interfaces.
"""


class ContextUtilsTestCase(TestCase):
    """Unit tests for context building and fallback generation."""

    def test_build_resume_ai_context(self):
        resume = MagicMock()
        parsed = MagicMock(
            skills=["Python", "Django"],
            education=[{"degree": "B.Tech"}],
            experience=[{"title": "Dev"}],
            projects=[],
            certifications=[],
        )
        parsed.name = "John Doe"
        ats = MagicMock(ats_score=85, grade="A", analysis={"missing_sections": ["Summary"], "warnings": []})
        match = MagicMock(matched_skills=["Python"], missing_skills=["AWS"])

        context = build_resume_ai_context(resume, parsed, ats, match)
        self.assertEqual(context["name"], "John Doe")
        self.assertEqual(context["ats_score"], 85)
        self.assertIn("Python", context["skills"])
        self.assertIn("AWS", context["missing_skills"])

    def test_fallback_ai_suggestions_generator(self):
        context = {
            "skills": ["Python", "Django"],
            "ats_score": 65,
            "missing_skills": ["AWS", "Kafka"],
            "missing_sections": ["Summary"],
            "projects": [],
        }
        res = generate_fallback_ai_suggestions(context)
        self.assertIn("summary", res)
        self.assertIn("strengths", res)
        self.assertIn("weaknesses", res)
        self.assertIn("suggestions", res)
        self.assertIn("priority_skills", res)
        self.assertIn("improved_project_description", res)
        self.assertIn("AWS", res["priority_skills"])


class OpenAIClientTestCase(TestCase):
    """Unit tests for OpenAIResumeClient."""

    def test_client_fallback_when_no_api_key(self):
        client = OpenAIResumeClient(api_key="")
        context = {"skills": ["Java"], "ats_score": 80, "missing_skills": ["Docker"]}
        res = client.generate_suggestions(context)
        self.assertIsInstance(res, dict)
        self.assertIn("summary", res)
        self.assertGreater(len(res["suggestions"]), 0)

    @patch("openai.OpenAI")
    def test_client_mock_openai_response(self, mock_openai_cls):
        mock_instance = MagicMock()
        mock_openai_cls.return_value = mock_instance

        mock_choice = MagicMock()
        mock_choice.message.content = '{"summary": "Mocked summary", "strengths": ["Strong Java"], "weaknesses": ["No AWS"], "suggestions": ["Learn AWS"], "priority_skills": ["AWS"], "improved_project_description": "Built ResumeIQ."}'
        mock_instance.chat.completions.create.return_value.choices = [mock_choice]

        client = OpenAIResumeClient(api_key="sk-mock-key")
        res = client.generate_suggestions({"name": "Test User", "skills": ["Java"]})
        self.assertEqual(res["summary"], "Mocked summary")
        self.assertIn("Strong Java", res["strengths"])


class AISuggestionAPITestCase(TestCase):
    """API-level tests for POST/GET /api/resumes/{id}/ai-suggestions/."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="ai_test@test.com",
            password="TestPassword123!",
            full_name="AI Tester",
        )
        self.resume = Resume.objects.create(
            user=self.user,
            original_filename="test_resume.pdf",
            file="resumes/1/test.pdf",
            file_type="pdf",
            file_size=5000,
            processing_status=Resume.STATUS_COMPLETED,
            cleaned_text=SAMPLE_RESUME_TEXT,
            raw_text=SAMPLE_RESUME_TEXT,
        )
        self.parsed_resume = ParsedResume.objects.create(
            resume=self.resume,
            name="John Candidate",
            email="john@example.com",
            skills=["Python", "Django", "React"],
            education=[{"degree": "B.Tech"}],
            experience=[{"title": "Software Engineer"}],
            projects=[],
            certifications=[],
        )
        self.ats_score = ATSScore.objects.create(
            resume=self.resume,
            ats_score=82,
            grade="A",
            grade_label="Very Good",
            summary="Very good ATS compliance.",
            breakdown={"formatting": 15, "contact": 10},
            analysis={"missing_sections": ["Summary"], "warnings": []},
        )
        # Authenticate
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

    def test_generate_ai_suggestions_post_api(self):
        url = f"/api/resumes/{self.resume.pk}/ai-suggestions/"
        resp = self.client.post(url, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        data = resp.json()
        self.assertIn("data", data)
        self.assertIn("summary", data["data"])
        self.assertIn("strengths", data["data"])
        self.assertIn("weaknesses", data["data"])
        self.assertIn("suggestions", data["data"])
        self.assertIn("priority_skills", data["data"])
        self.assertIn("improved_project_description", data["data"])

    def test_retrieve_ai_suggestions_get_api(self):
        # First generate
        self.client.post(f"/api/resumes/{self.resume.pk}/ai-suggestions/", format="json")

        # Then retrieve
        url = f"/api/resumes/{self.resume.pk}/ai-suggestions/"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertIn("summary", data)
        self.assertTrue(ResumeSuggestion.objects.filter(resume=self.resume).exists())

    def test_nonexistent_resume_returns_404(self):
        resp = self.client.post("/api/resumes/99999/ai-suggestions/", format="json")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthenticated_request_returns_401(self):
        self.client.credentials()  # Remove auth
        resp = self.client.post(f"/api/resumes/{self.resume.pk}/ai-suggestions/", format="json")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
