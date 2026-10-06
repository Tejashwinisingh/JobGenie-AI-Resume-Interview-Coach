"""
apps/mock_interview/utils.py

Helper utilities for context building and rule-based question generation (offline mode).
"""
import json
from typing import Any, Dict, List, Tuple

from .constants import (
    CATEGORY_BEHAVIORAL,
    CATEGORY_CODING,
    CATEGORY_HR,
    CATEGORY_PROJECT,
    CATEGORY_RESUME,
    CATEGORY_TECHNICAL,
    TYPE_BEHAVIORAL,
    TYPE_CODING,
    TYPE_HR,
    TYPE_PROJECT,
    TYPE_TECHNICAL,
)


def _safe_str_join(items: List[Any], default: str = "None") -> str:
    """Safely convert a list of strings/dicts into a comma-separated string."""
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
                str(item)
            )
            result.append(str(val))
        else:
            result.append(str(item))
    return ", ".join(result) if result else default


def build_session_context(session) -> Dict[str, Any]:
    """
    Extract structured context from an InterviewSession and its Resume.

    Args:
        session: InterviewSession ORM object.

    Returns:
        Dict formatted for prompt generation.
    """
    resume = session.resume
    parsed = getattr(resume, "parsed_data", None)

    name = "Candidate"
    skills: List[Any] = []
    education: List[Any] = []
    experience: List[Any] = []
    projects: List[Any] = []

    if parsed:
        name = parsed.name or "Candidate"
        skills = parsed.skills or []
        education = parsed.education or []
        experience = parsed.experience or []
        projects = parsed.projects or []

    # Build previous history string
    history_lines = []
    previous_questions = session.questions.order_by("question_number")
    for q in previous_questions:
        ans_text = q.user_answer.strip() if q.user_answer else "[No response provided yet]"
        history_lines.append(
            f"Q{q.question_number} [{q.category}]: {q.question}\nAnswer: {ans_text}"
        )

    previous_history = "\n\n".join(history_lines) if history_lines else "No questions asked yet."

    skills_str_list = [
        s if isinstance(s, str) else (s.get("name", str(s)) if isinstance(s, dict) else str(s))
        for s in skills
    ]

    return {
        "name": name,
        "skills": _safe_str_join(skills, default="Not specified"),
        "education": json.dumps(education),
        "experience": json.dumps(experience),
        "projects": json.dumps(projects),
        "job_role": session.role,
        "difficulty": session.difficulty,
        "interview_type": session.interview_type,
        "question_number": session.current_question,
        "total_questions": session.total_questions,
        "previous_history": previous_history,
        "_skills_list": skills_str_list,
        "_projects_list": projects,
    }


def generate_fallback_question(context: Dict[str, Any]) -> Tuple[str, str]:
    """
    Rule-based fallback question generator for offline mode or when API key is missing.

    Returns:
        Tuple[category, question_text]
    """
    q_num = context.get("question_number", 1)
    role = context.get("job_role", "Software Developer")
    difficulty = context.get("difficulty", "Medium")
    itype = context.get("interview_type", "Mixed")
    skills = context.get("_skills_list", [])
    projects = context.get("_projects_list", [])
    history = context.get("previous_history", "")

    # If previous question was asked, check if we can do a follow-up
    last_q = None
    if "Answer:" in history:
        last_parts = history.split("Q")[-1]
        last_q = last_parts

    top_skill = skills[0] if skills else "Python"
    second_skill = skills[1] if len(skills) > 1 else "Django"

    # Category selection by type or sequence
    category = CATEGORY_TECHNICAL
    if itype == TYPE_HR:
        category = CATEGORY_HR
    elif itype == TYPE_BEHAVIORAL:
        category = CATEGORY_BEHAVIORAL
    elif itype == TYPE_CODING:
        category = CATEGORY_CODING
    elif itype == TYPE_PROJECT:
        category = CATEGORY_PROJECT
    elif itype == TYPE_TECHNICAL:
        category = CATEGORY_TECHNICAL
    else:
        # Mixed interview rotation
        rotation = [
            CATEGORY_HR,
            CATEGORY_TECHNICAL,
            CATEGORY_RESUME,
            CATEGORY_PROJECT,
            CATEGORY_CODING,
            CATEGORY_BEHAVIORAL,
        ]
        category = rotation[(q_num - 1) % len(rotation)]

    # Pool of questions by category
    question_text = ""

    if category == CATEGORY_HR:
        hr_pool = [
            f"Tell me about yourself and what brought you to apply for this {role} position.",
            f"Why do you think you are a good fit for this {role} role?",
            "What are your key strengths and what area are you currently trying to improve?",
            f"Where do you see your career progressing in 3 to 5 years as a {role}?",
            "What kind of work environment allows you to do your best work?",
        ]
        question_text = hr_pool[(q_num - 1) % len(hr_pool)]

    elif category == CATEGORY_TECHNICAL:
        tech_pool = [
            f"Explain the core concept of {top_skill} and how you use it in building {role} applications.",
            f"What is the difference between synchronous and asynchronous processing in {role} systems?",
            f"How do you design database indexes in PostgreSQL/MySQL for optimal performance?",
            "Explain REST API best practices for resource design, error handling, and status codes.",
            f"What are the trade-offs between monolithic architecture and microservices for a {role} project?",
            f"How do you handle authentication (JWT/OAuth2) and authorization in your backend APIs?",
        ]
        question_text = tech_pool[(q_num - 1) % len(tech_pool)]

    elif category == CATEGORY_RESUME:
        resume_pool = [
            f"Walk me through your most recent software project from your resume.",
            f"Looking at your background, what was the most technical feature you personally implemented?",
            f"Which technology listed on your resume ({top_skill}, {second_skill}) do you feel most proficient in and why?",
        ]
        question_text = resume_pool[(q_num - 1) % len(resume_pool)]

    elif category == CATEGORY_PROJECT:
        if projects and isinstance(projects[0], dict):
            pname = projects[0].get("name", projects[0].get("title", "your key project"))
            pdesc = projects[0].get("description", "")
            question_text = f"In your project '{pname}', how did you structure the architecture? What technical challenges did you encounter?"
        else:
            question_text = f"Describe a project you built as a {role}. What was your role, and how did you choose the tech stack?"

    elif category == CATEGORY_CODING:
        coding_pool = [
            f"Write a function in {top_skill} to check if a string is a valid palindrome, ignoring non-alphanumeric characters.",
            f"How would you implement a function to find the first non-repeating character in a string?",
            f"Write a algorithm in {top_skill} to merge two sorted arrays/lists in O(N) time.",
            "Write a SQL query to find duplicate records in a table based on an email column.",
        ]
        question_text = coding_pool[(q_num - 1) % len(coding_pool)]

    elif category == CATEGORY_BEHAVIORAL:
        behavioral_pool = [
            "Describe a situation where a technical project hit an unexpected obstacle or delay. How did you handle it?",
            "Tell me about a time you disagreed with a team member or tech lead on an architecture decision.",
            "Describe a time when you had to take on a task outside your comfort zone. What was the outcome?",
            "Tell me about a time you received constructive feedback. How did you incorporate it?",
        ]
        question_text = behavioral_pool[(q_num - 1) % len(behavioral_pool)]

    else:
        question_text = f"Tell me about your experience working with {top_skill} as a {role}."

    return category, question_text
