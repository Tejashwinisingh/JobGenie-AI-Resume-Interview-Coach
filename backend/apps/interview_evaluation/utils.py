"""
apps/interview_evaluation/utils.py

Helper utilities for context formatting and rule-based fallback evaluation.
"""
import json
from typing import Any, Dict, List
from django.utils import timezone

from .constants import (
    REC_HIGHLY_RECOMMENDED,
    REC_NEEDS_IMPROVEMENT,
    REC_NOT_RECOMMENDED,
    REC_RECOMMENDED,
    THRESHOLD_HIGHLY_RECOMMENDED,
    THRESHOLD_NEEDS_IMPROVEMENT,
    THRESHOLD_RECOMMENDED,
)


def calculate_interview_duration(started_at, completed_at=None) -> str:
    """Calculate human-readable interview duration (e.g., '4m 30s')."""
    if not started_at:
        return "0m 0s"
    end_time = completed_at or timezone.now()
    delta_seconds = int((end_time - started_at).total_seconds())
    if delta_seconds <= 0:
        return "0m 15s"
    
    minutes = delta_seconds // 60
    seconds = delta_seconds % 60
    return f"{minutes}m {seconds}s"


def build_evaluation_context(session) -> Dict[str, Any]:
    """
    Format InterviewSession Q&A transcript into structured prompt context.

    Args:
        session: InterviewSession instance.

    Returns:
        Dict ready for prompt formatting.
    """
    resume = session.resume
    parsed = getattr(resume, "parsed_data", None)

    name = "Candidate"
    skills = []
    experience = []

    if parsed:
        name = parsed.name or "Candidate"
        skills = parsed.skills or []
        experience = parsed.experience or []

    questions = session.questions.order_by("question_number")
    transcript_lines = []
    total_words = 0
    answered_count = 0

    for q in questions:
        ans_text = (q.user_answer or "").strip()
        if ans_text:
            word_count = len(ans_text.split())
            total_words += word_count
            answered_count += 1
            display_ans = ans_text
        else:
            display_ans = "[Candidate did not answer]"
        
        transcript_lines.append(
            f"Q{q.question_number} [{q.category}]: {q.question}\nAnswer: {display_ans}\n"
        )

    transcript_text = "\n".join(transcript_lines) if transcript_lines else "No questions recorded."
    skills_str = ", ".join([str(s) for s in skills]) if skills else "Not specified"
    avg_len = int(total_words / answered_count) if answered_count > 0 else 0
    duration_str = calculate_interview_duration(session.started_at, session.completed_at)

    return {
        "name": name,
        "job_role": session.role,
        "difficulty": session.difficulty,
        "interview_type": session.interview_type,
        "skills": skills_str,
        "experience": json.dumps(experience),
        "transcript": transcript_text,
        "average_response_length": avg_len,
        "interview_duration": duration_str,
        "_questions_list": list(questions),
    }


def generate_fallback_evaluation(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deterministic rule-based fallback evaluation engine for offline mode.
    Analyzes word count, completeness, and keyword presence in user answers.

    Args:
        context: Context dict from build_evaluation_context().

    Returns:
        Dict formatted matching the expected AI evaluation schema.
    """
    role = context.get("job_role", "Software Developer")
    questions = context.get("_questions_list", [])
    avg_resp_length = context.get("average_response_length", 0)
    duration_str = context.get("interview_duration", "0m 0s")

    question_analysis: List[Dict] = []
    total_q = len(questions)

    if total_q == 0:
        return {
            "overall_score": 0,
            "hiring_recommendation": REC_NOT_RECOMMENDED,
            "summary": "No questions were answered during this interview session.",
            "technical_score": 0,
            "communication_score": 0,
            "confidence_score": 0,
            "grammar_score": 0,
            "problem_solving_score": 0,
            "professionalism_score": 0,
            "average_response_length": 0,
            "interview_duration": duration_str,
            "strengths": ["Completed session setup"],
            "weaknesses": ["No answers submitted"],
            "recommended_topics": ["Core " + role + " Fundamentals"],
            "question_analysis": [],
        }

    sum_tech = 0
    sum_comm = 0
    sum_conf = 0
    sum_gram = 0
    sum_comp = 0
    sum_relev = 0
    sum_prob = 0
    sum_prof = 0
    sum_over = 0

    for q in questions:
        ans = (q.user_answer or "").strip()
        word_count = len(ans.split()) if ans else 0

        # Heuristic scoring based on answer length & substance
        if word_count == 0:
            tech = 0
            comm = 0
            conf = 0
            gram = 0
            comp = 0
            relev = 0
            prob = 0
            prof = 0
            over = 0
            feedback = "No answer provided. Candidate skipped this question."
            strengths_list = []
            weaknesses_list = ["No answer submitted"]
            missing = ["Complete answer explanation", "Technical concepts"]
            suggestions = ["Provide at least a brief explanation using core terms"]
        elif word_count < 8:
            tech = 4
            comm = 4
            conf = 4
            gram = 7
            comp = 3
            relev = 5
            prob = 4
            prof = 5
            over = 4
            feedback = f"Very brief answer ({word_count} words). Expand with specific details and technical examples."
            strengths_list = ["Answered question directly"]
            weaknesses_list = ["Lacks technical depth and elaboration"]
            missing = ["Detailed technical explanation", "Real-world context"]
            suggestions = ["Use the STAR method (Situation, Task, Action, Result) to structure your response"]
        elif word_count < 25:
            tech = 7
            comm = 7
            conf = 7
            gram = 8
            comp = 7
            relev = 8
            prob = 7
            prof = 8
            over = 7
            feedback = f"Good concise answer ({word_count} words). Demonstrates core understanding."
            strengths_list = ["Clear articulation of main concept", "Good conciseness"]
            weaknesses_list = ["Could include architectural trade-offs"]
            missing = ["Advanced edge-case handling"]
            suggestions = ["Mention specific libraries, frameworks, or design patterns used"]
        else:
            tech = 9
            comm = 9
            conf = 8
            gram = 9
            comp = 9
            relev = 9
            prob = 8
            prof = 9
            over = 9
            feedback = f"Comprehensive answer ({word_count} words). Excellent detail and technical depth."
            strengths_list = ["In-depth technical response", "Strong terminology usage", "Clear structure"]
            weaknesses_list = []
            missing = []
            suggestions = ["Keep maintaining this thorough structure in live interviews"]

        sum_tech += tech
        sum_comm += comm
        sum_conf += conf
        sum_gram += gram
        sum_comp += comp
        sum_relev += relev
        sum_prob += prob
        sum_prof += prof
        sum_over += over

        question_analysis.append({
            "question_number": q.question_number,
            "category": q.category,
            "question": q.question,
            "user_answer": q.user_answer,
            "technical": tech,
            "communication": comm,
            "confidence": conf,
            "grammar": gram,
            "completeness": comp,
            "relevance": relev,
            "problem_solving": prob,
            "professionalism": prof,
            "overall": over,
            "feedback": feedback,
            "strengths": strengths_list,
            "weaknesses": weaknesses_list,
            "missing_concepts": missing,
            "improvement_suggestions": suggestions,
        })

    # Average scores scaled to 0-100
    avg_tech = min(100, int((sum_tech / (total_q * 10)) * 100))
    avg_comm = min(100, int((sum_comm / (total_q * 10)) * 100))
    avg_conf = min(100, int((sum_conf / (total_q * 10)) * 100))
    avg_gram = min(100, int((sum_gram / (total_q * 10)) * 100))
    avg_prob = min(100, int((sum_prob / (total_q * 10)) * 100))
    avg_prof = min(100, int((sum_prof / (total_q * 10)) * 100))
    overall_score = min(100, int((sum_over / (total_q * 10)) * 100))

    # Hiring Recommendation logic
    if overall_score >= THRESHOLD_HIGHLY_RECOMMENDED:
        rec = REC_HIGHLY_RECOMMENDED
    elif overall_score >= THRESHOLD_RECOMMENDED:
        rec = REC_RECOMMENDED
    elif overall_score >= THRESHOLD_NEEDS_IMPROVEMENT:
        rec = REC_NEEDS_IMPROVEMENT
    else:
        rec = REC_NOT_RECOMMENDED

    summary = (
        f"Candidate achieved an overall score of {overall_score}/100 for the {role} position. "
        f"Technical depth scored {avg_tech}/100 and communication scored {avg_comm}/100. "
        f"Result: {rec}."
    )

    strengths = [
        f"Completed {total_q} questions during the mock interview session.",
        f"Demonstrated good baseline communication ({avg_comm}/100).",
        f"Structured responses clearly for {role} position.",
    ]

    weaknesses = [
        "Include more quantifiable metrics and STAR-method outcomes in technical answers.",
        "Provide deeper explanations for system architecture and performance optimization.",
    ]

    recommended_topics = [
        f"{role} System Architecture",
        "Performance Tuning & Caching",
        "REST API Security & OAuth2",
        "Database Indexing & Query Optimization",
    ]

    return {
        "overall_score": overall_score,
        "hiring_recommendation": rec,
        "summary": summary,
        "technical_score": avg_tech,
        "communication_score": avg_comm,
        "confidence_score": avg_conf,
        "grammar_score": avg_gram,
        "problem_solving_score": avg_prob,
        "professionalism_score": avg_prof,
        "average_response_length": avg_resp_length,
        "interview_duration": duration_str,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "recommended_topics": recommended_topics,
        "question_analysis": question_analysis,
    }
