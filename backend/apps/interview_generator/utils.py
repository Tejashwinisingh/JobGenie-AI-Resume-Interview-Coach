"""
apps/interview_generator/utils.py

Utility functions for building interview context and generating
rule-based fallback questions when no API key is available.
"""
import json
from typing import Any, Dict, List

from .constants import (
    CATEGORY_BEHAVIORAL,
    CATEGORY_CODING,
    CATEGORY_HR,
    CATEGORY_PROJECT,
    CATEGORY_RESUME,
    CATEGORY_TECHNICAL,
    CATEGORY_DISTRIBUTION,
    DEFAULT_QUESTION_COUNT,
)


def _safe_str_join(items: List[Any], default: str = "None") -> str:
    """Safely convert a list of strings/dicts/scalars into a comma-separated string."""
    if not items:
        return default
    result = []
    for item in items:
        if isinstance(item, str):
            result.append(item)
        elif isinstance(item, dict):
            val = (
                item.get("name") or
                item.get("title") or
                item.get("degree") or
                item.get("certification") or
                str(item)
            )
            result.append(str(val))
        else:
            result.append(str(item))
    return ", ".join(result) if result else default


def build_interview_context(
    resume,
    job_role: str,
    difficulty: str,
    count: int,
) -> Dict[str, Any]:
    """
    Build a structured context dict from a Resume ORM object for prompt formatting.

    Args:
        resume: Resume model instance (with parsed_data, ats_score related objects).
        job_role: Desired job role string.
        difficulty: "Easy" | "Medium" | "Hard"
        count: Number of questions to generate.

    Returns:
        Dict ready for use in USER_PROMPT_TEMPLATE.format(**context).
    """
    # ── Parsed Resume ────────────────────────────────────────────────────────
    parsed = getattr(resume, 'parsed_data', None)
    name = "Candidate"
    skills: List[Any] = []
    education: List[Any] = []
    experience: List[Any] = []
    projects: List[Any] = []
    certifications: List[Any] = []

    if parsed:
        name = parsed.name or "Candidate"
        skills = parsed.skills or []
        education = parsed.education or []
        experience = parsed.experience or []
        projects = parsed.projects or []
        certifications = parsed.certifications or []

    # ── ATS Context ─────────────────────────────────────────────────────────
    ats_score = 0
    try:
        ats_obj = resume.ats_score
        ats_score = ats_obj.ats_score if ats_obj else 0
    except Exception:
        ats_score = 0

    # ── Job Match Context ────────────────────────────────────────────────────
    matched_skills: List[str] = []
    missing_skills: List[str] = []
    try:
        latest_match = resume.match_reports.order_by('-created_at').first()
        if latest_match:
            matched_skills = latest_match.matched_skills or []
            missing_skills = latest_match.missing_skills or []
    except Exception:
        pass

    # ── Category Distribution String ─────────────────────────────────────────
    distribution = CATEGORY_DISTRIBUTION.get(count, CATEGORY_DISTRIBUTION[DEFAULT_QUESTION_COUNT])
    dist_str = "\n".join(
        f"  - {cat}: {n} question(s)" for cat, n in distribution.items()
    )

    # ── Project Names ────────────────────────────────────────────────────────
    project_names_list = []
    for p in (projects or []):
        if isinstance(p, dict):
            project_names_list.append(p.get("name") or p.get("title") or "Project")
        elif isinstance(p, str):
            project_names_list.append(p)
    project_names = ", ".join(project_names_list) if project_names_list else "No specific projects mentioned"

    # ── Top Skills for Coding ─────────────────────────────────────────────────
    skills_str_list = [
        s if isinstance(s, str) else (s.get("name", str(s)) if isinstance(s, dict) else str(s))
        for s in skills
    ]
    top_skills = ", ".join(skills_str_list[:8]) if skills_str_list else "Python, Django"

    return {
        "name": name,
        "skills": _safe_str_join(skills, default="Not specified"),
        "education": json.dumps(education),
        "experience": json.dumps(experience),
        "projects": json.dumps(projects),
        "certifications": _safe_str_join(certifications, default="None"),
        "job_role": job_role,
        "difficulty": difficulty,
        "count": count,
        "ats_score": ats_score,
        "matched_skills": _safe_str_join(matched_skills, default="N/A"),
        "missing_skills": _safe_str_join(missing_skills, default="N/A"),
        "category_distribution": dist_str,
        "project_names": project_names,
        "top_skills": top_skills,
        # Store raw lists for fallback generator
        "_skills_list": skills_str_list,
        "_projects_list": projects,
        "_experience_list": experience,
    }


# ─── Rule-Based Fallback Generator ──────────────────────────────────────────

def generate_fallback_questions(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate interview questions using deterministic rules when no API key is set.
    Ensures the module works offline / without OpenRouter or OpenAI.
    """
    job_role = context.get("job_role", "Software Developer")
    difficulty = context.get("difficulty", "Medium")
    count = context.get("count", 10)
    skills = context.get("_skills_list", [])
    projects = context.get("_projects_list", [])

    questions: List[Dict] = []
    qid = 1

    distribution = CATEGORY_DISTRIBUTION.get(count, CATEGORY_DISTRIBUTION[10])

    # ── HR Questions ─────────────────────────────────────────────────────────
    hr_pool = [
        f"Tell me about yourself and why you are interested in the {job_role} role.",
        f"Why should we hire you for this {job_role} position?",
        "What are your greatest professional strengths?",
        "What do you consider your biggest weakness and how are you working on it?",
        f"Where do you see yourself in 5 years as a {job_role}?",
    ]
    for q in hr_pool[:distribution.get(CATEGORY_HR, 2)]:
        questions.append({"id": qid, "category": CATEGORY_HR, "question": q})
        qid += 1

    # ── Technical Questions ──────────────────────────────────────────────────
    tech_templates = [
        f"Explain the core principles of {job_role} development you follow.",
        f"How do you approach designing a scalable {job_role} system?",
        f"Explain REST APIs and how you have used them in your projects.",
        "What is the difference between SQL and NoSQL databases? When would you choose each?",
        "Explain the concept of microservices and its advantages over a monolith.",
        f"How do you handle authentication and authorization in your {job_role} projects?",
        "Explain CI/CD pipeline and how it improves development workflow.",
    ]
    if skills:
        tech_templates.insert(0, f"Explain your experience with {skills[0]} and how you have used it.")
        if len(skills) > 1:
            tech_templates.insert(1, f"What are the key differences between {skills[0]} and {skills[1]}?")
    for q in tech_templates[:distribution.get(CATEGORY_TECHNICAL, 3)]:
        questions.append({"id": qid, "category": CATEGORY_TECHNICAL, "question": q})
        qid += 1

    # ── Resume Questions ─────────────────────────────────────────────────────
    resume_qs = [
        f"Walk me through your resume and highlight your most relevant experience for this {job_role} role.",
        "What is the most challenging technical problem you solved at a previous company?",
        "Which of your past roles best prepared you for this position and why?",
    ]
    for q in resume_qs[:distribution.get(CATEGORY_RESUME, 2)]:
        questions.append({"id": qid, "category": CATEGORY_RESUME, "question": q})
        qid += 1

    # ── Project Questions ────────────────────────────────────────────────────
    if projects:
        for proj in projects[:distribution.get(CATEGORY_PROJECT, 2)]:
            if isinstance(proj, dict):
                pname = proj.get("name", proj.get("title", "your project"))
            else:
                pname = str(proj)
            questions.append({
                "id": qid,
                "category": CATEGORY_PROJECT,
                "question": f"Explain the architecture and tech stack of your project '{pname}'. What challenges did you face?",
            })
            qid += 1
    else:
        pq = distribution.get(CATEGORY_PROJECT, 1)
        for _ in range(pq):
            questions.append({
                "id": qid,
                "category": CATEGORY_PROJECT,
                "question": f"Describe a significant project you built as a {job_role}. Walk me through your architecture decisions.",
            })
            qid += 1

    # ── Coding Questions ─────────────────────────────────────────────────────
    lang = 'Python'
    if skills:
        first_skill = str(skills[0])
        if 'Python' in skills:
            lang = 'Python'
        else:
            lang = first_skill

    coding_qs = [
        f"Write a function in {lang} to find all duplicate elements in a list.",
        "Design a REST API endpoint for user authentication with JWT. Explain the complete request/response flow.",
        "How would you implement a rate limiter for an API endpoint? Describe the algorithm.",
        "Write a SQL query to find the top 5 most active users from a transactions table.",
    ]
    for q in coding_qs[:distribution.get(CATEGORY_CODING, 1)]:
        questions.append({"id": qid, "category": CATEGORY_CODING, "question": q})
        qid += 1

    # ── Behavioral Questions ─────────────────────────────────────────────────
    behavioral_qs = [
        "Describe a time you faced a difficult technical challenge. How did you approach it using the STAR method?",
        "Tell me about a conflict you had with a team member and how you resolved it.",
        "Describe a situation where you had to meet a tight deadline. How did you prioritize?",
        "Tell me about a time you received critical feedback and how you handled it.",
    ]
    for q in behavioral_qs[:distribution.get(CATEGORY_BEHAVIORAL, 1)]:
        questions.append({"id": qid, "category": CATEGORY_BEHAVIORAL, "question": q})
        qid += 1

    # Trim to exact count
    questions = questions[:count]

    return {
        "job_role": job_role,
        "difficulty": difficulty,
        "questions": questions,
    }
