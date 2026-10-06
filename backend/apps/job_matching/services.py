"""
apps/job_matching/services.py

JobMatchingService — Service layer for Job Description processing and matching.

Provides:
  - create_job_description(): Ingests text/PDF/DOCX, cleans text, parses requirements, and saves model.
  - match_resume_to_jd(): Runs matching engine, persists JobMatch model.
  - get_or_create_match(): Retrieves existing match or triggers fresh match calculation.
"""
import os
import re
import fitz  # PyMuPDF
import docx  # python-docx
from typing import Optional

from apps.resumes.services import ResumeTextExtractorService
from .models import JobDescription, JobMatch
from .parser import JobDescriptionParser
from .engine import JobMatchingEngine


class JobMatchingService:
    """
    Service layer coordinating text extraction, parsing, engine execution, and persistence.
    """

    @staticmethod
    def extract_text_from_file(file_obj, file_type: str) -> str:
        """
        Extract raw text from uploaded PDF or DOCX file.
        """
        if file_type == JobDescription.FILE_TYPE_PDF:
            file_bytes = file_obj.read()
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            text_parts = []
            for page in doc:
                text_parts.append(page.get_text())
            doc.close()
            return "\n".join(text_parts)

        elif file_type == JobDescription.FILE_TYPE_DOCX:
            doc = docx.Document(file_obj)
            text_parts = [para.text for para in doc.paragraphs if para.text]
            return "\n".join(text_parts)

        return ""

    @staticmethod
    def clean_text(raw_text: str) -> str:
        """
        Clean control characters and normalize whitespace.
        """
        if not raw_text:
            return ""
        # Remove null bytes and non-printable control chars
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", raw_text)
        # Collapse multiple blank lines
        text = re.sub(r"\n\s*\n+", "\n\n", text)
        return text.strip()

    @classmethod
    def create_job_description(
        cls,
        user,
        title: str,
        company: str = "",
        description: str = "",
        file_obj=None,
    ) -> JobDescription:
        """
        Create a new Job Description record.

        Args:
            user: Authenticated User model instance.
            title: Job Title.
            company: Company Name (optional).
            description: Raw pasted description text (optional if file provided).
            file_obj: Uploaded File instance (PDF or DOCX, optional).

        Returns:
            JobDescription instance with extracted & parsed requirements.
        """
        file_type = JobDescription.FILE_TYPE_TEXT
        raw_text = description or ""

        if file_obj:
            _, ext = os.path.splitext(file_obj.name.lower())
            if ext == ".pdf":
                file_type = JobDescription.FILE_TYPE_PDF
                raw_text = cls.extract_text_from_file(file_obj, file_type)
            elif ext == ".docx":
                file_type = JobDescription.FILE_TYPE_DOCX
                raw_text = cls.extract_text_from_file(file_obj, file_type)

        cleaned_text = cls.clean_text(raw_text)
        parsed_data = JobDescriptionParser.parse_jd(cleaned_text, title=title)

        jd = JobDescription.objects.create(
            user=user,
            title=parsed_data.get("title") or title or "Job Position",
            company=company,
            description=description,
            file=file_obj,
            file_type=file_type,
            raw_text=raw_text,
            cleaned_text=cleaned_text,
            parsed_data=parsed_data,
        )
        return jd

    @classmethod
    def match_resume_to_jd(cls, job_description: JobDescription, resume) -> JobMatch:
        """
        Run matching engine on a resume vs job description and persist result.

        Args:
            job_description: JobDescription instance.
            resume: Resume instance (must have cleaned_text or raw_text).

        Returns:
            JobMatch model instance.
        """
        # Ensure resume has extracted text and parsed data
        if not (resume.cleaned_text or resume.raw_text):
            ResumeTextExtractorService.process_resume(resume)
            resume.refresh_from_db()

        if not hasattr(resume, "parsed_data") or resume.parsed_data is None:
            ResumeTextExtractorService.parse_and_store_resume(resume)
            resume.refresh_from_db()

        parsed_resume = getattr(resume, "parsed_data", None)

        engine = JobMatchingEngine()
        result = engine.run(resume, parsed_resume, job_description)

        job_match, _ = JobMatch.objects.update_or_create(
            job_description=job_description,
            resume=resume,
            defaults={
                "match_score": result.match_score,
                "grade": result.grade,
                "matched_skills": result.matched_skills,
                "missing_skills": result.missing_skills,
                "extra_skills": result.extra_skills,
                "experience_score": result.experience_score,
                "education_score": result.education_score,
                "certification_score": result.certification_score,
                "keyword_score": result.keyword_score,
                "breakdown": result.breakdown,
            },
        )
        return job_match
