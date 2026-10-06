"""
apps/job_matching/parser.py

JobDescriptionParser — Deterministic parser for Job Description text.

Extracts:
  - Job Title
  - Required Skills
  - Preferred Skills
  - Experience Required (years)
  - Education Required (degree)
  - Certifications Required
  - Technologies Mentioned
"""
import re
from typing import Dict, Any, List

from apps.ats.constants import TECHNICAL_SKILLS, ALL_KEYWORDS
from .utils import parse_experience_years


class JobDescriptionParser:
    """
    Parses unstructured Job Description text into structured requirements.

    Usage:
        parsed_data = JobDescriptionParser.parse_jd(cleaned_text, title="...")
    """

    @staticmethod
    def parse_jd(text: str, title: str = "") -> Dict[str, Any]:
        """
        Parse job description text into structured components.

        Args:
            text: Cleaned job description text.
            title: Job title string if provided by user.

        Returns:
            Dict containing:
                - title: Job title
                - required_skills: List[str]
                - preferred_skills: List[str]
                - experience_years: float
                - required_degree: str
                - certifications: List[str]
                - technologies: List[str]
        """
        text = text or ""
        text_lower = text.lower()

        # ── 1. Job Title ───────────────────────────────────────────────────
        extracted_title = title.strip()
        if not extracted_title:
            # Fallback: look for lines starting with "Role:", "Title:", "Job Title:"
            title_match = re.search(
                r"(?:job title|title|role|position)\s*[:\-]\s*([^\n]+)",
                text,
                re.IGNORECASE,
            )
            if title_match:
                extracted_title = title_match.group(1).strip()
            else:
                # Use first non-empty line as fallback title
                lines = [line.strip() for line in text.split("\n") if line.strip()]
                extracted_title = lines[0] if lines else "Unspecified Job Title"

        # ── 2. Skills Extraction ──────────────────────────────────────────
        found_skills: List[str] = []
        for kw in ALL_KEYWORDS:
            kw_lower = kw.lower()
            if " " in kw:
                pattern = re.escape(kw_lower)
            else:
                pattern = rf"\b{re.escape(kw_lower)}\b"

            if re.search(pattern, text_lower):
                found_skills.append(kw)

        # Separate required vs preferred skills if sections exist
        required_skills = found_skills
        preferred_skills: List[str] = []

        preferred_section = re.search(
            r"(?:preferred|nice to have|plus|desired)\s+(?:skills|qualifications|requirements)[^\n]*\n(.*?)(?:\n\n|\Z)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if preferred_section:
            pref_text = preferred_section.group(1).lower()
            preferred_skills = [
                sk for sk in found_skills if sk.lower() in pref_text
            ]
            required_skills = [
                sk for sk in found_skills if sk not in preferred_skills
            ]

        # ── 3. Experience Years ───────────────────────────────────────────
        experience_years = parse_experience_years(text)

        # ── 4. Education Required ─────────────────────────────────────────
        required_degree = ""
        degree_patterns = [
            (r"\b(ph\.?d|doctorate)\b", "PhD"),
            (r"\b(m\.?tech|master\'?s?|m\.?s|mca|m\.?sc|mba)\b", "Master's Degree"),
            (r"\b(b\.?tech|bachelor\'?s?|b\.?e|b\.?sc|bca|b\.?s)\b", "Bachelor's Degree"),
            (r"\b(diploma|associate)\b", "Diploma"),
        ]
        for pattern, deg_name in degree_patterns:
            if re.search(pattern, text_lower):
                required_degree = deg_name
                break

        # ── 5. Certifications ─────────────────────────────────────────────
        certs_found: List[str] = []
        cert_keywords = [
            "aws certified", "azure certified", "gcp certified", "pmp",
            "cissp", "ceh", "scrum master", "csm", "ckad", "cka",
            "oracle certified", "istqb", "comptia",
        ]
        for cert in cert_keywords:
            if cert in text_lower:
                certs_found.append(cert.title())

        return {
            "title": extracted_title,
            "required_skills": required_skills,
            "preferred_skills": preferred_skills,
            "experience_years": experience_years,
            "required_degree": required_degree,
            "certifications": certs_found,
            "technologies": found_skills,
        }
