"""
apps/ai_resume/utils.py

Context formatting utilities and offline fallback generator for AI Resume Suggestions.
"""
from typing import Dict, Any, List


def build_resume_ai_context(resume, parsed_resume=None, ats_score_obj=None, job_match_obj=None) -> Dict[str, Any]:
    """
    Format candidate resume, ATS score, and job match details into structured context.
    """
    p_data = getattr(parsed_resume, "__dict__", {}) if parsed_resume else {}

    skills = getattr(parsed_resume, "skills", []) if parsed_resume else []
    education = getattr(parsed_resume, "education", []) if parsed_resume else []
    experience = getattr(parsed_resume, "experience", []) if parsed_resume else []
    projects = getattr(parsed_resume, "projects", []) if parsed_resume else []
    certs = getattr(parsed_resume, "certifications", []) if parsed_resume else []
    name = getattr(parsed_resume, "name", "") if parsed_resume else ""

    ats_score = getattr(ats_score_obj, "ats_score", 0) if ats_score_obj else 0
    ats_grade = getattr(ats_score_obj, "grade", "N/A") if ats_score_obj else "N/A"

    analysis = getattr(ats_score_obj, "analysis", {}) or {} if ats_score_obj else {}
    missing_sections = analysis.get("missing_sections", [])
    ats_warnings = analysis.get("warnings", [])

    matched_skills = getattr(job_match_obj, "matched_skills", []) if job_match_obj else []
    missing_skills = getattr(job_match_obj, "missing_skills", []) if job_match_obj else []

    return {
        "name": name or "Candidate",
        "skills": skills,
        "education": education,
        "experience": experience,
        "projects": projects,
        "certifications": certs,
        "ats_score": ats_score,
        "ats_grade": ats_grade,
        "missing_sections": missing_sections,
        "ats_warnings": ats_warnings,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
    }


def generate_fallback_ai_suggestions(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate deterministic rule-based AI suggestions when OpenAI API is offline or unconfigured.
    """
    skills: List[str] = context.get("skills", [])
    ats_score: int = context.get("ats_score", 0)
    missing_skills: List[str] = context.get("missing_skills", [])
    missing_sections: List[str] = context.get("missing_sections", [])
    projects: List[Dict[str, Any]] = context.get("projects", [])

    strengths = []
    weaknesses = []
    suggestions = []

    # Analyze strengths
    if len(skills) >= 5:
        strengths.append(f"Strong foundation across {len(skills)} technical skills.")
    else:
        strengths.append("Clear technical skill presentation.")

    if len(projects) > 0:
        strengths.append(f"Hands-on project experience with {len(projects)} project(s).")
    else:
        strengths.append("Structured educational background.")

    if ats_score >= 70:
        strengths.append("Good ATS compliance and formatting structure.")

    # Analyze weaknesses
    if ats_score < 70:
        weaknesses.append("ATS formatting score is below recommended 70% threshold.")

    if missing_sections:
        weaknesses.append(f"Missing recommended resume section(s): {', '.join(missing_sections[:3])}.")

    if missing_skills:
        weaknesses.append(f"Lacks key job skills: {', '.join(missing_skills[:3])}.")
    elif len(skills) < 8:
        weaknesses.append("Skill density could be expanded to match industry expectations.")

    # Formulate suggestions
    suggestions.append("Quantify project accomplishments using metrics (e.g. 'Improved efficiency by 30%').")
    suggestions.append("Ensure standard section headers (Skills, Experience, Education, Projects) are clearly labelled.")

    if missing_skills:
        suggestions.append(f"Add experience or projects demonstrating: {', '.join(missing_skills[:3])}.")
    else:
        suggestions.append("Add links to live projects or GitHub repositories for developer credibility.")

    suggestions.append("Use strong action verbs (e.g. Developed, Architected, Automated) for bullet points.")
    suggestions.append("Deduplicate redundant skill listings and organize them by category.")

    # Priority learning roadmap
    priority_skills = missing_skills[:4] if missing_skills else ["Docker", "AWS", "CI/CD", "Redis"]

    # Sample improved project description
    proj_title = projects[0].get("title", "Full Stack Application") if projects else "ResumeIQ Platform"
    improved_desc = (
        f"Architected and deployed {proj_title} using modular architecture; "
        "implemented JWT authentication, automated text extraction, and REST API endpoints, "
        "resulting in a 40% improvement in candidate screening efficiency."
    )

    summary = (
        f"Candidate resume scored {ats_score}/100 on ATS quality check. "
        "The technical foundation is solid, but adding quantifiable metrics and key domain skills will maximize interview callbacks."
    )

    return {
        "summary": summary,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "suggestions": suggestions,
        "priority_skills": priority_skills,
        "improved_project_description": improved_desc,
    }
