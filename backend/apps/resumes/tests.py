"""
apps/resumes/tests.py

Unit tests for the resumes module (upload, list, delete, replace, text extraction, & parsing).
Run with: python manage.py test apps.resumes
"""
import io
import os
import fitz
import docx
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
# pyrefly: ignore [missing-import]
from rest_framework import status
# pyrefly: ignore [missing-import]
from rest_framework.test import APITestCase
# pyrefly: ignore [missing-import]
from rest_framework_simplejwt.tokens import RefreshToken

from apps.authentication.models import User
from .models import Resume, ParsedResume
from .services import ResumeTextExtractorService
from .parser import ResumeParser


def make_valid_pdf():
    """Return a real, parseable PDF file created with PyMuPDF."""
    doc = fitz.open()
    page = doc.new_page()
    content = (
        "Alex Turner\n"
        "alex.turner@example.com | +1 555 123 4567 | linkedin.com/in/alex-turner | github.com/alex-turner\n\n"
        "SKILLS\n"
        "Python, Django, React, PostgreSQL, Docker, AWS, Git, REST API\n\n"
        "EXPERIENCE\n"
        "Senior Software Engineer\n"
        "Tech Solutions Inc | 2021 - Present\n"
        "- Architected RESTful microservices using Python and Django.\n"
        "- Deployed applications on AWS using Docker containers.\n\n"
        "EDUCATION\n"
        "Bachelor of Science in Computer Science\n"
        "University of California | 2017 - 2021\n\n"
        "PROJECTS\n"
        "ResumeIQ - AI Resume Parsing Platform\n"
        "Built full stack application with React, Django, and PostgreSQL.\n\n"
        "CERTIFICATIONS\n"
        "AWS Certified Solutions Architect\n"
    )
    page.insert_text((50, 50), content)
    pdf_bytes = doc.tobytes()
    doc.close()
    return SimpleUploadedFile('alex_turner_resume.pdf', pdf_bytes, content_type='application/pdf')


def make_valid_docx():
    """Return a real, parseable DOCX file created with python-docx."""
    doc = docx.Document()
    doc.add_heading('Jane Smith', 0)
    doc.add_paragraph('jane.smith@example.com | github.com/janesmith')
    doc.add_paragraph('SKILLS:\nReact, TypeScript, Node.js, MongoDB, Docker')
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return SimpleUploadedFile('jane_smith_resume.docx', buffer.getvalue(),
                              content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')


def make_txt():
    """Return a fake TXT file (invalid type)."""
    return SimpleUploadedFile('bad_file.txt', b'Hello world', content_type='text/plain')


class ResumeUploadTests(APITestCase):
    """Tests for POST /api/resumes/"""

    list_url = '/api/resumes/'

    def setUp(self):
        self.user = User.objects.create_user(
            email='resume_user@example.com',
            password='TestPass123!',
            full_name='Resume User',
        )
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

    def tearDown(self):
        for resume in Resume.objects.filter(user=self.user):
            resume.delete()

    def test_upload_pdf_success(self):
        response = self.client.post(self.list_url, {'file': make_valid_pdf()}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('resume', response.data)
        self.assertEqual(response.data['resume']['file_type'], 'pdf')
        self.assertEqual(response.data['resume']['processing_status'], Resume.STATUS_COMPLETED)
        self.assertTrue(response.data['resume']['has_extracted_text'])
        self.assertTrue(response.data['resume']['has_parsed_data'])

    def test_upload_docx_success(self):
        response = self.client.post(self.list_url, {'file': make_valid_docx()}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['resume']['file_type'], 'docx')
        self.assertTrue(response.data['resume']['has_parsed_data'])

    def test_upload_invalid_type_rejected(self):
        response = self.client.post(self.list_url, {'file': make_txt()}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Resume.objects.filter(user=self.user).count(), 0)

    def test_upload_requires_auth(self):
        self.client.credentials()
        response = self.client.post(self.list_url, {'file': make_valid_pdf()}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ResumeListTests(APITestCase):
    """Tests for GET /api/resumes/"""

    list_url = '/api/resumes/'

    def setUp(self):
        self.user = User.objects.create_user(
            email='list_user@example.com',
            password='TestPass123!',
            full_name='List User',
        )
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

    def tearDown(self):
        for resume in Resume.objects.filter(user=self.user):
            resume.delete()

    def test_list_empty(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_list_after_upload(self):
        self.client.post(self.list_url, {'file': make_valid_pdf()}, format='multipart')
        self.client.post(self.list_url, {'file': make_valid_docx()}, format='multipart')
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)


class ResumeParsingTests(APITestCase):
    """Tests for Module 4 Parsing Engine and APIs"""

    list_url = '/api/resumes/'

    def setUp(self):
        self.user = User.objects.create_user(
            email='parse_user@example.com',
            password='TestPass123!',
            full_name='Parse User',
        )
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

    def tearDown(self):
        for resume in Resume.objects.filter(user=self.user):
            resume.delete()

    def test_parser_unit_methods(self):
        sample_text = (
            "Alex Turner\n"
            "Email: alex.turner@example.com | Phone: +1 555 123 4567\n"
            "LinkedIn: linkedin.com/in/alex-turner | GitHub: github.com/alex-turner\n"
            "SKILLS\nPython, Django, React, PostgreSQL, Docker, AWS"
        )
        parsed = ResumeParser.parse_resume(sample_text)
        self.assertEqual(parsed['name'], 'Alex Turner')
        self.assertEqual(parsed['email'], 'alex.turner@example.com')
        self.assertIn('555', parsed['phone'])
        self.assertEqual(parsed['linkedin'], 'https://linkedin.com/in/alex-turner')
        self.assertEqual(parsed['github'], 'https://github.com/alex-turner')
        self.assertIn('Python', parsed['skills'])
        self.assertIn('Django', parsed['skills'])
        self.assertIn('React', parsed['skills'])
        self.assertIn('PostgreSQL', parsed['skills'])

    def test_parse_and_get_parsed_api_endpoints(self):
        # 1. Upload PDF
        res = self.client.post(self.list_url, {'file': make_valid_pdf()}, format='multipart')
        resume_id = res.data['resume']['id']

        # 2. Trigger Parse Endpoint (POST /api/resumes/<id>/parse/)
        parse_url = f'/api/resumes/{resume_id}/parse/'
        parse_res = self.client.post(parse_url)
        self.assertEqual(parse_res.status_code, status.HTTP_200_OK)
        data = parse_res.data['data']
        self.assertEqual(data['email'], 'alex.turner@example.com')
        self.assertIn('Python', data['skills'])
        self.assertIn('Django', data['skills'])
        self.assertGreater(len(data['education']), 0)

        # 3. Retrieve Parsed Data Endpoint (GET /api/resumes/<id>/parsed/)
        get_parsed_url = f'/api/resumes/{resume_id}/parsed/'
        get_res = self.client.get(get_parsed_url)
        self.assertEqual(get_res.status_code, status.HTTP_200_OK)
        self.assertEqual(get_res.data['email'], 'alex.turner@example.com')
        self.assertIn('AWS', get_res.data['skills'])

    def test_parsed_endpoint_nonexistent_returns_404(self):
        res = self.client.get('/api/resumes/9999/parsed/')
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
