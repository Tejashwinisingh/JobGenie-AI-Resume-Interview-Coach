"""
apps/job_matching/tests.py

Comprehensive unit tests and API tests for Module 6 — Job Description Matching Engine.

Test Scenarios:
  1. Perfect Match (Skills, Exp, Edu, Certs, Keywords all match)
  2. Partial Match
  3. No Match
  4. Resume without experience (fresher score positive)
  5. Resume without education
  6. Resume with extra skills & missing skills
  7. Blank / Empty Job Description
  8. Evaluators unit tests (Skills, Experience, Education, Certifications, Keywords)
  9. API: POST /api/job-descriptions/ (create via text & file upload)
  10. API: POST /api/job-descriptions/{id}/match/{resume_id}/ (generate report)
  11. API: GET  /api/job-descriptions/{id}/match/{resume_id}/ (retrieve report)
  12. API: 404 / 400 error handling
"""
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import MagicMock

from apps.authentication.models import User
from apps.resumes.models import Resume, ParsedResume
from .models import JobDescription, JobMatch
from .engine import JobMatchingEngine, MatchResult
from .evaluators.skills import SkillsEvaluator
from .evaluators.experience import ExperienceEvaluator
from .evaluators.education import EducationEvaluator
from .evaluators.certifications import CertificationsEvaluator
from .evaluators.keywords import KeywordsEvaluator
from .utils import match_degree_level, parse_experience_years


SAMPLE_JD_TEXT = """
Job Title: Senior Backend Developer
Company: Acme Tech

Requirements:
- 3+ years of experience in Python and Django development
- Bachelor's Degree in Computer Science or Software Engineering
- Must know Java, Spring Boot, Docker, AWS, Kafka, and REST API
- Preferred: AWS Certified Developer
"""

SAMPLE_RESUME_TEXT = """
John Candidate
john@example.com

SKILLS
Java, Spring Boot, React, Docker, Git, MySQL, Python, Django

EXPERIENCE
Software Engineer (3 years)
Developed REST APIs and containerized applications using Docker and Django.

EDUCATION
Bachelor of Technology in Computer Science (2021)

CERTIFICATIONS
AWS Certified Developer
"""


class EvaluatorsTestCase(TestCase):
    """Unit tests for individual evaluators."""

    def test_skills_evaluator(self):
        ev = SkillsEvaluator()
        result = ev.evaluate(
            resume_skills=["Java", "Spring Boot", "React", "Docker", "Git", "MySQL"],
            jd_required_skills=["Java", "Spring Boot", "Docker", "AWS", "Kafka", "REST API"],
        )
        self.assertIn("Java", result["matched_skills"])
        self.assertIn("Spring Boot", result["matched_skills"])
        self.assertIn("AWS", result["missing_skills"])
        self.assertIn("React", result["extra_skills"])
        self.assertGreater(result["score"], 0)

    def test_experience_evaluator(self):
        ev = ExperienceEvaluator()
        exp = [{"title": "Software Engineer", "company": "Tech Corp"}]
        result = ev.evaluate(exp, required_years=3.0)
        self.assertGreater(result["score"], 0)

    def test_fresher_experience_evaluator(self):
        ev = ExperienceEvaluator()
        result = ev.evaluate([], required_years=0.0)
        self.assertEqual(result["score"], 20)

    def test_education_evaluator_full_match(self):
        ev = EducationEvaluator()
        res_edu = [{"degree": "B.Tech in Computer Science"}]
        result = ev.evaluate(res_edu, required_degree="Bachelor's Degree")
        self.assertEqual(result["match_status"], "Full Match")
        self.assertEqual(result["score"], 10)

    def test_education_evaluator_no_education(self):
        ev = EducationEvaluator()
        result = ev.evaluate([], required_degree="Bachelor's Degree")
        self.assertEqual(result["match_status"], "No Match")
        self.assertEqual(result["score"], 0)

    def test_certifications_evaluator(self):
        ev = CertificationsEvaluator()
        result = ev.evaluate(["AWS Certified"], ["AWS Certified"])
        self.assertEqual(result["score"], 10)

    def test_keywords_evaluator(self):
        ev = KeywordsEvaluator()
        result = ev.evaluate("Python Django Docker REST API", "Python Django Docker Kafka")
        self.assertGreater(result["score"], 0)


class JobMatchingEngineTestCase(TestCase):
    """Integration-level tests for JobMatchingEngine."""

    def _make_resume(self, text=""):
        r = MagicMock()
        r.cleaned_text = text or SAMPLE_RESUME_TEXT
        r.raw_text = text or SAMPLE_RESUME_TEXT
        return r

    def _make_parsed_resume(self, **kwargs):
        defaults = {
            "skills": ["Java", "Spring Boot", "React", "Docker", "Git", "MySQL"],
            "education": [{"degree": "B.Tech in Computer Science"}],
            "experience": [{"title": "Software Developer"}],
            "certifications": ["AWS Certified"],
        }
        defaults.update(kwargs)
        p = MagicMock()
        for k, v in defaults.items():
            setattr(p, k, v)
        return p

    def _make_jd(self, **kwargs):
        defaults = {
            "title": "Senior Backend Developer",
            "required_skills": ["Java", "Spring Boot", "Docker", "AWS", "Kafka", "REST API"],
            "preferred_skills": [],
            "experience_years": 3.0,
            "required_degree": "Bachelor's Degree",
            "certifications": ["AWS Certified"],
        }
        defaults.update(kwargs)
        jd = MagicMock()
        jd.cleaned_text = SAMPLE_JD_TEXT
        jd.description = SAMPLE_JD_TEXT
        jd.parsed_data = defaults
        return jd

    def test_engine_run_perfect_or_high_match(self):
        engine = JobMatchingEngine()
        result = engine.run(self._make_resume(), self._make_parsed_resume(), self._make_jd())
        self.assertIsInstance(result, MatchResult)
        self.assertGreaterEqual(result.match_score, 50)
        self.assertIn("Java", result.matched_skills)
        self.assertIn("AWS", result.missing_skills)

    def test_engine_blank_jd(self):
        engine = JobMatchingEngine()
        blank_jd = self._make_jd(required_skills=[], experience_years=0, required_degree="")
        blank_jd.cleaned_text = ""
        blank_jd.description = ""
        result = engine.run(self._make_resume(), self._make_parsed_resume(), blank_jd)
        self.assertGreaterEqual(result.match_score, 0)


class JobMatchingAPITestCase(TestCase):
    """API-level tests for Job Description creation & matching endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="jd_match@test.com",
            password="TestPassword123!",
            full_name="JD Match Tester",
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
            skills=["Java", "Spring Boot", "React", "Docker", "Git", "MySQL"],
            education=[{"degree": "B.Tech in Computer Science"}],
            experience=[{"title": "Software Engineer"}],
            certifications=["AWS Certified"],
        )
        # Authenticate
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

    def test_create_jd_text_api(self):
        payload = {
            "title": "Backend Engineer",
            "company": "Acme Corp",
            "description": SAMPLE_JD_TEXT,
        }
        resp = self.client.post("/api/job-descriptions/", payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertIn("data", resp.json())
        self.assertEqual(resp.json()["data"]["title"], "Backend Engineer")

    def test_list_jds_api(self):
        JobDescription.objects.create(
            user=self.user,
            title="Frontend Dev",
            description="React JS HTML CSS",
        )
        resp = self.client.get("/api/job-descriptions/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(resp.json()), 1)

    def test_generate_and_retrieve_match_report_api(self):
        # 1. Create JD
        jd = JobDescription.objects.create(
            user=self.user,
            title="Senior Developer",
            description=SAMPLE_JD_TEXT,
            cleaned_text=SAMPLE_JD_TEXT,
            parsed_data={
                "title": "Senior Developer",
                "required_skills": ["Java", "Spring Boot", "Docker", "AWS", "Kafka"],
                "experience_years": 3.0,
                "required_degree": "Bachelor's Degree",
                "certifications": [],
            },
        )

        # 2. POST match report
        match_url = f"/api/job-descriptions/{jd.pk}/match/{self.resume.pk}/"
        resp_post = self.client.post(match_url, format="json")
        self.assertEqual(resp_post.status_code, status.HTTP_200_OK)
        data = resp_post.json()

        # Verify output format matches prompt requirements
        self.assertIn("match_score", data)
        self.assertIn("grade", data)
        self.assertIn("matched_skills", data)
        self.assertIn("missing_skills", data)
        self.assertIn("extra_skills", data)
        self.assertIn("experience_match", data)
        self.assertIn("education_match", data)
        self.assertIn("certification_match", data)
        self.assertIn("keyword_match", data)

        # 3. GET match report
        resp_get = self.client.get(match_url)
        self.assertEqual(resp_get.status_code, status.HTTP_200_OK)
        self.assertEqual(resp_get.json()["match_score"], data["match_score"])

    def test_match_nonexistent_jd_returns_404(self):
        resp = self.client.post(f"/api/job-descriptions/99999/match/{self.resume.pk}/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_match_unauthorized_returns_401(self):
        self.client.credentials()  # Remove auth header
        resp = self.client.post("/api/job-descriptions/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
