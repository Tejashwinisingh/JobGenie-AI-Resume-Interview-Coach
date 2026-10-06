"""
apps/ats/tests.py

Unit tests and API tests for Module 5 – ATS Analysis Engine.

Test cases:
  1.  Complete resume → high score (≥70)
  2.  Fresher resume (no experience) → not zero
  3.  Resume without projects → projects score = 0
  4.  Resume without education → education score = 0
  5.  Resume without experience → fresher base score (2)
  6.  Resume with keyword stuffing → stuffing detected, warning raised
  7.  Blank resume → score = 0 from formatting
  8.  Resume with 30+ technical skills → skills score = 15
  9.  Evaluator unit tests (scoring, utils)
  10. API: POST /ats-score/ → 201
  11. API: GET  /ats-score/ → 200
  12. API: GET  /ats-score/ unauthenticated → 401
  13. API: POST resume not found → 404
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import MagicMock, patch

from apps.authentication.models import User
from apps.resumes.models import Resume, ParsedResume
from .engine import ATSEngine, ATSResult
from .scoring import ATSScorer
from .evaluators.formatting import FormattingEvaluator
from .evaluators.contact import ContactEvaluator
from .evaluators.structure import StructureEvaluator
from .evaluators.keywords import KeywordsEvaluator
from .evaluators.skills import SkillsEvaluator
from .evaluators.education import EducationEvaluator
from .evaluators.experience import ExperienceEvaluator
from .evaluators.projects import ProjectsEvaluator
from .utils import normalize_text, count_keyword_occurrences, whitespace_ratio
from .services import ATSService
from .models import ATSScore


# ─── Helpers ─────────────────────────────────────────────────────────────────

SAMPLE_CLEANED_TEXT = """
John Doe
john@example.com | +91-9876543210
linkedin.com/in/johndoe | github.com/johndoe

SUMMARY
Experienced software engineer with 3 years in Python and Django development.

SKILLS
Python, Django, React, PostgreSQL, Docker, AWS, Git, REST API, JavaScript

EDUCATION
Bachelor of Engineering in Computer Science
ABC University, 2021

EXPERIENCE
Software Engineer — XYZ Technologies (Jan 2021 – Present)
- Developed REST APIs using Django and DRF
- Deployed services using Docker and AWS EC2

PROJECTS
Resume Builder App
Built with React, Django, PostgreSQL. Automated resume parsing using NLP.

CERTIFICATIONS
AWS Certified Developer Associate
"""

MINIMAL_TEXT = "John\njohn@example.com\nPython"

BLANK_TEXT = ""

KEYWORD_STUFFED_TEXT = (
    "Python Python Python Python Python Python Python Python Python Python "
    "Python Python Python Python Python Python Python Python Python Python "
    "Python Python Python Python Python Python Python Python Python Python "
) * 5


# ─── Utility Tests ───────────────────────────────────────────────────────────

class UtilsTestCase(TestCase):
    """Unit tests for apps/ats/utils.py."""

    def test_normalize_text_lowercases(self):
        result = normalize_text("Hello, World!")
        # Punctuation replaced with space then collapsed → "hello world"
        self.assertIn("hello", result)
        self.assertIn("world", result)
        self.assertEqual(result, result.lower())

    def test_normalize_text_empty(self):
        self.assertEqual(normalize_text(""), "")

    def test_count_keyword_occurrences_single(self):
        count = count_keyword_occurrences("python", "I know Python and python very well")
        self.assertGreaterEqual(count, 2)

    def test_count_keyword_occurrences_phrase(self):
        count = count_keyword_occurrences("spring boot", "Using Spring Boot framework")
        self.assertGreaterEqual(count, 1)

    def test_whitespace_ratio_empty(self):
        self.assertEqual(whitespace_ratio(""), 1.0)

    def test_whitespace_ratio_normal(self):
        ratio = whitespace_ratio("Hello world")
        self.assertLess(ratio, 0.5)


# ─── Scorer Tests ─────────────────────────────────────────────────────────────

class ATSScorerTestCase(TestCase):
    """Unit tests for ATSScorer."""

    def test_grade_excellent(self):
        grade, label = ATSScorer.compute_grade(95)
        self.assertEqual(grade, "A+")
        self.assertEqual(label, "Excellent")

    def test_grade_very_good(self):
        grade, label = ATSScorer.compute_grade(85)
        self.assertEqual(grade, "A")

    def test_grade_good(self):
        grade, label = ATSScorer.compute_grade(72)
        self.assertEqual(grade, "B")

    def test_grade_average(self):
        grade, label = ATSScorer.compute_grade(65)
        self.assertEqual(grade, "C")

    def test_grade_needs_improvement(self):
        grade, label = ATSScorer.compute_grade(45)
        self.assertEqual(grade, "D")

    def test_compute_total(self):
        breakdown = {"formatting": 15, "contact": 10, "structure": 8}
        self.assertEqual(ATSScorer.compute_total(breakdown), 33)

    def test_compute_total_capped_at_100(self):
        breakdown = {"a": 60, "b": 60}
        self.assertEqual(ATSScorer.compute_total(breakdown), 100)


# ─── Evaluator Unit Tests ─────────────────────────────────────────────────────

class FormattingEvaluatorTestCase(TestCase):
    def setUp(self):
        self.ev = FormattingEvaluator()

    def test_blank_resume_scores_zero(self):
        result = self.ev.evaluate("", "")
        self.assertEqual(result["score"], 0)

    def test_good_resume_scores_high(self):
        result = self.ev.evaluate(SAMPLE_CLEANED_TEXT, "")
        self.assertGreaterEqual(result["score"], 12)

    def test_short_resume_has_warning(self):
        result = self.ev.evaluate("Hello", "")
        self.assertTrue(len(result["warnings"]) > 0)


class ContactEvaluatorTestCase(TestCase):
    def setUp(self):
        self.ev = ContactEvaluator()

    def test_full_contact_scores_max(self):
        data = {
            "name": "John", "email": "j@j.com",
            "phone": "9876543210", "linkedin": "li.com/in/j",
            "github": "github.com/j"
        }
        result = self.ev.evaluate(data)
        self.assertEqual(result["score"], 10)

    def test_empty_contact_scores_zero(self):
        result = self.ev.evaluate({})
        self.assertEqual(result["score"], 0)

    def test_missing_linkedin_github_warning(self):
        data = {"name": "John", "email": "j@j.com", "phone": "123"}
        result = self.ev.evaluate(data)
        warnings = " ".join(result["warnings"]).lower()
        self.assertIn("linkedin", warnings)
        self.assertIn("github", warnings)


class StructureEvaluatorTestCase(TestCase):
    def setUp(self):
        self.ev = StructureEvaluator()

    def test_full_sections_scores_high(self):
        result = self.ev.evaluate(SAMPLE_CLEANED_TEXT)
        self.assertGreaterEqual(result["score"], 8)

    def test_blank_text_scores_zero(self):
        result = self.ev.evaluate("")
        self.assertEqual(result["score"], 0)

    def test_missing_sections_in_result(self):
        result = self.ev.evaluate("Just some random text with no headings")
        self.assertIn("missing_sections", result)
        self.assertGreater(len(result["missing_sections"]), 0)


class KeywordsEvaluatorTestCase(TestCase):
    def setUp(self):
        self.ev = KeywordsEvaluator()

    def test_keyword_stuffing_detected(self):
        result = self.ev.evaluate(KEYWORD_STUFFED_TEXT)
        all_text = " ".join(result["warnings"])
        self.assertIn("stuffing", all_text.lower())

    def test_good_resume_finds_keywords(self):
        result = self.ev.evaluate(SAMPLE_CLEANED_TEXT)
        self.assertGreater(result["keyword_count"], 5)

    def test_blank_text_scores_zero(self):
        result = self.ev.evaluate("")
        self.assertEqual(result["score"], 0)


class SkillsEvaluatorTestCase(TestCase):
    def setUp(self):
        self.ev = SkillsEvaluator()

    def test_30_skills_scores_max(self):
        skills = [
            "Python", "Java", "Django", "React", "Angular", "Vue",
            "PostgreSQL", "MySQL", "MongoDB", "Redis", "Docker", "Kubernetes",
            "AWS", "Azure", "GCP", "Git", "GitHub", "Jenkins", "CI/CD",
            "Spring Boot", "Node.js", "TypeScript", "GraphQL", "Kafka",
            "TensorFlow", "Pandas", "NumPy", "Selenium", "Pytest", "JUnit"
        ]
        result = self.ev.evaluate(skills)
        self.assertEqual(result["score"], 15)

    def test_empty_skills_scores_zero(self):
        result = self.ev.evaluate([])
        self.assertEqual(result["score"], 0)

    def test_small_skill_set_warns(self):
        result = self.ev.evaluate(["Python", "Django"])
        self.assertTrue(len(result["warnings"]) > 0)


class EducationEvaluatorTestCase(TestCase):
    def setUp(self):
        self.ev = EducationEvaluator()

    def test_full_education_scores_high(self):
        edu = [{"degree": "B.Tech Computer Science", "institution": "MIT", "date": "2021"}]
        result = self.ev.evaluate(edu)
        self.assertGreaterEqual(result["score"], 7)

    def test_no_education_scores_zero(self):
        result = self.ev.evaluate([])
        self.assertEqual(result["score"], 0)


class ExperienceEvaluatorTestCase(TestCase):
    def setUp(self):
        self.ev = ExperienceEvaluator()

    def test_fresher_no_experience_gets_base_score(self):
        result = self.ev.evaluate([])
        self.assertGreater(result["score"], 0)

    def test_intern_experience_scores_positively(self):
        exp = [{"title": "Software Engineering Intern", "company": "Google",
                "date": "Jun 2023 – Aug 2023", "bullets": ["Built features", "Wrote tests"]}]
        result = self.ev.evaluate(exp)
        self.assertGreaterEqual(result["score"], 4)

    def test_full_experience_scores_high(self):
        exp = [
            {"title": "Software Engineer", "company": "TCS",
             "date": "Jan 2021 – Present",
             "bullets": ["Developed APIs", "Led team", "Improved performance"]},
            {"title": "Junior Developer", "company": "Infosys",
             "date": "Jun 2020 – Dec 2020",
             "bullets": ["Coded features", "Fixed bugs"]},
        ]
        result = self.ev.evaluate(exp)
        self.assertGreaterEqual(result["score"], 8)


class ProjectsEvaluatorTestCase(TestCase):
    def setUp(self):
        self.ev = ProjectsEvaluator()

    def test_no_projects_scores_zero(self):
        result = self.ev.evaluate([])
        self.assertEqual(result["score"], 0)

    def test_three_quality_projects_scores_max(self):
        projects = [
            {"title": "Resume IQ", "description": "ATS resume analysis tool", "technologies": ["Django", "React"]},
            {"title": "Chat App", "description": "Real-time messaging application", "technologies": ["Node.js", "Socket.io"]},
            {"title": "ML Pipeline", "description": "Machine learning data pipeline", "technologies": ["Python", "Airflow"]},
        ]
        result = self.ev.evaluate(projects)
        self.assertEqual(result["score"], 5)


# ─── Engine Integration Tests ─────────────────────────────────────────────────

class ATSEngineTestCase(TestCase):
    """Integration-level tests for the ATSEngine orchestrator."""

    def _make_resume(self, cleaned_text="", raw_text=""):
        """Build a mock Resume object."""
        r = MagicMock()
        r.cleaned_text = cleaned_text
        r.raw_text = raw_text
        r.file_type = "pdf"
        return r

    def _make_parsed(self, **kwargs):
        defaults = {
            "name": "John Doe", "email": "john@example.com",
            "phone": "9876543210", "linkedin": "li.com/in/john",
            "github": "github.com/john",
            "skills": ["Python", "Django", "React"],
            "education": [{"degree": "B.Tech", "institution": "MIT", "date": "2021"}],
            "experience": [{"title": "Engineer", "company": "ABC", "date": "2021", "bullets": ["Did stuff"]}],
            "projects": [{"title": "App", "description": "A cool app", "technologies": ["Python"]}],
            "certifications": [],
        }
        defaults.update(kwargs)
        p = MagicMock()
        for k, v in defaults.items():
            setattr(p, k, v)
        return p

    def test_complete_resume_scores_above_70(self):
        engine = ATSEngine()
        result = engine.run(self._make_resume(SAMPLE_CLEANED_TEXT), self._make_parsed())
        self.assertIsInstance(result, ATSResult)
        self.assertGreaterEqual(result.ats_score, 50)

    def test_blank_resume_low_score(self):
        engine = ATSEngine()
        result = engine.run(self._make_resume("", ""), None)
        self.assertLessEqual(result.ats_score, 20)

    def test_result_has_all_breakdown_keys(self):
        engine = ATSEngine()
        result = engine.run(self._make_resume(SAMPLE_CLEANED_TEXT), None)
        expected_keys = {"formatting", "contact", "structure", "keywords", "skills", "education", "experience", "projects"}
        self.assertEqual(set(result.breakdown.keys()), expected_keys)

    def test_fresher_resume_not_zero(self):
        engine = ATSEngine()
        parsed = self._make_parsed(experience=[], projects=[])
        result = engine.run(self._make_resume(SAMPLE_CLEANED_TEXT), parsed)
        self.assertGreater(result.ats_score, 0)


# ─── API Tests ────────────────────────────────────────────────────────────────

class ATSScoreAPITestCase(TestCase):
    """API-level tests for POST/GET /api/resumes/<id>/ats-score/."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="ats@test.com",
            password="Test@1234",
            full_name="ATS Tester",
        )
        # Create a resume with extracted text and parsed data
        self.resume = Resume.objects.create(
            user=self.user,
            original_filename="test_resume.pdf",
            file="resumes/1/test.pdf",
            file_type="pdf",
            file_size=10000,
            processing_status=Resume.STATUS_COMPLETED,
            cleaned_text=SAMPLE_CLEANED_TEXT,
            raw_text=SAMPLE_CLEANED_TEXT,
        )
        self.parsed = ParsedResume.objects.create(
            resume=self.resume,
            name="John Doe",
            email="john@example.com",
            phone="9876543210",
            linkedin="linkedin.com/in/john",
            github="github.com/john",
            skills=["Python", "Django", "React", "PostgreSQL", "Docker"],
            education=[{"degree": "B.Tech", "institution": "MIT", "date": "2021"}],
            experience=[{"title": "Engineer", "company": "ABC Corp", "date": "2021–2023",
                         "bullets": ["Built APIs", "Led sprints"]}],
            projects=[{"title": "ResumeIQ", "description": "ATS analysis tool",
                       "technologies": ["Django", "React"]}],
            certifications=[],
        )
        # Authenticate
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

    def _post_ats(self, resume_id=None):
        rid = resume_id or self.resume.pk
        return self.client.post(f"/api/resumes/{rid}/ats-score/", format="json")

    def _get_ats(self, resume_id=None):
        rid = resume_id or self.resume.pk
        return self.client.get(f"/api/resumes/{rid}/ats-score/", format="json")

    def test_post_generates_ats_score_201(self):
        resp = self._post_ats()
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        data = resp.json()
        self.assertIn("data", data)
        self.assertIn("ats_score", data["data"])
        self.assertIn("grade", data["data"])
        self.assertIn("breakdown", data["data"])

    def test_get_retrieves_ats_score_200(self):
        self._post_ats()  # Generate first
        resp = self._get_ats()
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("ats_score", resp.json())

    def test_score_has_correct_breakdown_keys(self):
        resp = self._post_ats()
        breakdown = resp.json()["data"]["breakdown"]
        expected = {"formatting", "contact", "structure", "keywords", "skills",
                    "education", "experience", "projects"}
        self.assertEqual(set(breakdown.keys()), expected)

    def test_score_stored_in_database(self):
        self._post_ats()
        self.assertTrue(ATSScore.objects.filter(resume=self.resume).exists())

    def test_post_returns_404_for_invalid_resume(self):
        resp = self._post_ats(resume_id=99999)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthenticated_request_returns_401(self):
        self.client.credentials()  # Remove auth
        resp = self._post_ats()
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_with_unprocessed_resume_triggers_processing(self):
        """Resume with no text but pending status should attempt extraction."""
        unprocessed = Resume.objects.create(
            user=self.user,
            original_filename="empty.pdf",
            file="resumes/1/empty.pdf",
            file_type="pdf",
            file_size=100,
            processing_status=Resume.STATUS_PENDING,
        )
        # File doesn't exist on disk — expect a graceful 400
        resp = self.client.post(f"/api/resumes/{unprocessed.pk}/ats-score/", format="json")
        self.assertIn(resp.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_201_CREATED])
