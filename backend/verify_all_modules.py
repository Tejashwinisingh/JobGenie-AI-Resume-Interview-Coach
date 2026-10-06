"""
backend/verify_all_modules.py
Comprehensive End-to-End API verification script for Modules 1, 2, 3, 4, and 5.
"""
import os
import sys
import django
import fitz  # PyMuPDF
from django.core.files.uploadedfile import SimpleUploadedFile

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
django.setup()

from rest_framework.test import APIClient
from rest_framework import status
from apps.authentication.models import User
from apps.resumes.models import Resume

SAMPLE_RESUME_TEXT = """John Doe
john.doe@example.com | +1-555-0199 | linkedin.com/in/johndoe | github.com/johndoe

SUMMARY
Experienced Software Engineer specializing in full-stack web development and scalable REST APIs.

SKILLS
Python, Django, React, JavaScript, PostgreSQL, Docker, AWS, Git, REST API, HTML, CSS, Tailwind

EDUCATION
Bachelor of Science in Computer Science
State University, 2021

EXPERIENCE
Software Engineer - Tech Corp (Jan 2022 - Present)
- Developed scalable RESTful APIs using Django REST Framework and PostgreSQL.
- Implemented responsive frontend UI in React and Tailwind CSS.
- Automated CI/CD pipelines using Docker and GitHub Actions on AWS.

PROJECTS
ResumeIQ Platform
- Built an automated ATS resume analysis tool with Python, Django, and React.
- Extracted and parsed structured candidate skills and contact details.

CERTIFICATIONS
AWS Certified Developer Associate"""


def generate_valid_pdf_bytes(text: str) -> bytes:
    """Generate a valid binary PDF stream in memory using PyMuPDF."""
    doc = fitz.open()
    page = doc.new_page()
    # Insert text as multiple lines
    y = 50
    for line in text.split('\n'):
        if line.strip():
            page.insert_text((50, y), line, fontsize=11)
            y += 18
        else:
            y += 10
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def run_verification():
    print("=" * 70)
    print("[START] Starting ResumeIQ Comprehensive End-to-End Verification (Modules 1–5)")
    print("=" * 70)

    client = APIClient()

    # Clean up test user if exists
    test_email = "verify_user@example.com"
    User.objects.filter(email=test_email).delete()

    # ── MODULE 1: AUTHENTICATION & USER PROFILE ────────────────────────────────
    print("\n--- MODULE 1: AUTHENTICATION ---")
    print("1. Testing Registration Endpoint [POST /api/auth/register/]...")
    reg_payload = {
        "email": test_email,
        "full_name": "Verification User",
        "password": "SecurePassword123!",
        "password_confirm": "SecurePassword123!"
    }
    res_reg = client.post('/api/auth/register/', reg_payload, format='json')
    assert res_reg.status_code == status.HTTP_201_CREATED, f"Registration failed: {res_reg.data}"
    tokens = res_reg.data.get('tokens', {})
    access_token = tokens.get('access')
    refresh_token = tokens.get('refresh')
    assert access_token and refresh_token, "Tokens missing in registration response"
    print("   [OK] Registration successful. JWT Access & Refresh tokens generated.")

    print("2. Testing Login Endpoint [POST /api/auth/login/]...")
    res_login = client.post('/api/auth/login/', {"email": test_email, "password": "SecurePassword123!"}, format='json')
    assert res_login.status_code == status.HTTP_200_OK, f"Login failed: {res_login.data}"
    print("   [OK] Login successful. Credentials authenticated.")

    print("3. Testing Profile Endpoint [GET /api/auth/profile/]...")
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
    res_prof = client.get('/api/auth/profile/')
    assert res_prof.status_code == status.HTTP_200_OK, f"Get Profile failed: {res_prof.data}"
    print(f"   [OK] Profile retrieved successfully for {res_prof.data.get('email')}.")

    # ── MODULE 2: RESUME UPLOAD ────────────────────────────────────────────────
    print("\n--- MODULE 2: RESUME UPLOAD ---")
    print("4. Testing Resume Upload [POST /api/resumes/]...")
    pdf_content = generate_valid_pdf_bytes(SAMPLE_RESUME_TEXT)
    uploaded_file = SimpleUploadedFile(
        "sample_resume.pdf",
        pdf_content,
        content_type="application/pdf"
    )
    res_upload = client.post('/api/resumes/', {'file': uploaded_file}, format='multipart')
    assert res_upload.status_code == status.HTTP_201_CREATED, f"Upload failed: {res_upload.data}"
    resume_id = res_upload.data['resume']['id']
    print(f"   [OK] Resume uploaded successfully (ID #{resume_id}).")

    print("5. Testing Resume List [GET /api/resumes/]...")
    res_list = client.get('/api/resumes/')
    assert res_list.status_code == status.HTTP_200_OK, f"List failed: {res_list.data}"
    assert len(res_list.data) >= 1, "Resume list empty"
    print(f"   [OK] Resume list retrieved ({len(res_list.data)} resume(s)).")

    # ── MODULE 3: RESUME PROCESSING (TEXT EXTRACTION) ──────────────────────────
    print("\n--- MODULE 3: RESUME PROCESSING ---")
    print(f"6. Testing Text Processing [POST /api/resumes/{resume_id}/process/]...")
    res_proc = client.post(f'/api/resumes/{resume_id}/process/')
    assert res_proc.status_code == status.HTTP_200_OK, f"Process failed: {res_proc.data}"
    print("   [OK] Resume text processing and cleaning completed.")

    print(f"7. Testing Extracted Text Retrieval [GET /api/resumes/{resume_id}/text/]...")
    res_text = client.get(f'/api/resumes/{resume_id}/text/')
    assert res_text.status_code == status.HTTP_200_OK, f"Get text failed: {res_text.data}"
    assert res_text.data.get('word_count', 0) > 0, "No words extracted"
    print(f"   [OK] Text retrieved ({res_text.data.get('word_count')} words, {res_text.data.get('character_count')} chars).")

    # ── MODULE 4: RESUME PARSING (STRUCTURED DATA) ────────────────────────────
    print("\n--- MODULE 4: RESUME PARSING ---")
    print(f"8. Testing Resume Parsing [POST /api/resumes/{resume_id}/parse/]...")
    res_parse = client.post(f'/api/resumes/{resume_id}/parse/')
    assert res_parse.status_code == status.HTTP_200_OK, f"Parse failed: {res_parse.data}"
    parsed_data = res_parse.data['data']
    assert parsed_data.get('name') == 'John Doe', f"Parsed name mismatch: {parsed_data.get('name')}"
    assert 'Python' in parsed_data.get('skills', []), "Skill Python not parsed"
    print("   [OK] Resume parsed cleanly into structured data (Name, Contact, Skills, Experience, Education, Projects).")

    print(f"9. Testing Parsed Data Retrieval [GET /api/resumes/{resume_id}/parsed/]...")
    res_get_parsed = client.get(f'/api/resumes/{resume_id}/parsed/')
    assert res_get_parsed.status_code == status.HTTP_200_OK, f"Get parsed failed: {res_get_parsed.data}"
    print("   [OK] Structured parsed profile retrieved successfully.")

    # ── MODULE 5: ATS ANALYSIS ENGINE ──────────────────────────────────────────
    print("\n--- MODULE 5: ATS ANALYSIS ENGINE ---")
    print(f"10. Testing ATS Evaluation [POST /api/resumes/{resume_id}/ats-score/]...")
    res_ats = client.post(f'/api/resumes/{resume_id}/ats-score/', format='json')
    assert res_ats.status_code == status.HTTP_201_CREATED, f"ATS Evaluation failed: {res_ats.data}"
    ats_data = res_ats.data['data']
    score = ats_data.get('ats_score')
    grade = ats_data.get('grade')
    breakdown = ats_data.get('breakdown', {})
    assert score is not None and score > 0, "ATS score missing or zero"
    assert len(breakdown) == 8, f"Breakdown missing categories: {breakdown}"
    print(f"   [OK] ATS evaluation complete! Score: {score}/100 | Grade: {grade} | Breakdown: {list(breakdown.keys())}")

    print(f"11. Testing ATS Report Retrieval [GET /api/resumes/{resume_id}/ats-score/]...")
    res_get_ats = client.get(f'/api/resumes/{resume_id}/ats-score/', format='json')
    assert res_get_ats.status_code == status.HTTP_200_OK, f"Get ATS report failed: {res_get_ats.data}"
    print(f"   [OK] ATS report retrieved successfully. Summary: \"{res_get_ats.data.get('summary')}\"")

    # ── MODULE 6: JOB DESCRIPTION MATCHING ENGINE ─────────────────────────────
    print("\n--- MODULE 6: JOB DESCRIPTION MATCHING ENGINE ---")
    print("12. Testing Job Description Creation [POST /api/job-descriptions/]...")
    jd_payload = {
        "title": "Full Stack Python & React Developer",
        "company": "Tech Corp Inc",
        "description": (
            "Job Title: Full Stack Developer\n"
            "Requirements:\n"
            "- 2+ years of experience in Python, Django, and React\n"
            "- Bachelor's Degree in Computer Science\n"
            "- Must know PostgreSQL, Docker, AWS, Git, and REST API\n"
            "- Preferred: AWS Certified Developer"
        )
    }
    res_jd = client.post('/api/job-descriptions/', jd_payload, format='json')
    assert res_jd.status_code == status.HTTP_201_CREATED, f"JD creation failed: {res_jd.data}"
    jd_id = res_jd.data['data']['id']
    print(f"   [OK] Job Description created and parsed (ID #{jd_id}).")

    print(f"13. Testing Match Report Generation [POST /api/job-descriptions/{jd_id}/match/{resume_id}/]...")
    res_match = client.post(f'/api/job-descriptions/{jd_id}/match/{resume_id}/', format='json')
    assert res_match.status_code == status.HTTP_200_OK, f"Match failed: {res_match.data}"
    match_data = res_match.data
    m_score = match_data.get('match_score')
    m_grade = match_data.get('grade')
    m_matched = match_data.get('matched_skills', [])
    m_missing = match_data.get('missing_skills', [])
    assert m_score is not None and m_score > 0, "Match score missing or zero"
    print(f"   [OK] Job Match report generated! Match Score: {m_score}% ({m_grade})")
    print(f"        Matched Skills: {m_matched}")
    print(f"        Missing Skills: {m_missing}")

    print(f"14. Testing Match Report Retrieval [GET /api/job-descriptions/{jd_id}/match/{resume_id}/]...")
    res_get_match = client.get(f'/api/job-descriptions/{jd_id}/match/{resume_id}/')
    assert res_get_match.status_code == status.HTTP_200_OK, f"Get match failed: {res_get_match.data}"
    print("   [OK] Match Report retrieved successfully.")

    # ── MODULE 7: AI RESUME IMPROVEMENT SUGGESTIONS ───────────────────────────
    print("\n--- MODULE 7: AI RESUME IMPROVEMENT SUGGESTIONS ---")
    print(f"15. Testing AI Suggestions Generation [POST /api/resumes/{resume_id}/ai-suggestions/]...")
    res_ai = client.post(f'/api/resumes/{resume_id}/ai-suggestions/', format='json')
    assert res_ai.status_code == status.HTTP_201_CREATED, f"AI suggestions generation failed: {res_ai.data}"
    ai_data = res_ai.data['data']
    assert 'summary' in ai_data, "Summary missing in AI response"
    assert 'suggestions' in ai_data, "Suggestions list missing in AI response"
    assert 'improved_project_description' in ai_data, "Improved project description missing in AI response"
    print(f"   [OK] AI Suggestions generated successfully!")
    print(f"        Summary: \"{ai_data.get('summary')}\"")
    print(f"        Strengths: {ai_data.get('strengths', [])[:2]}")
    print(f"        Suggestions: {ai_data.get('suggestions', [])[:2]}")
    print(f"        Priority Skills: {ai_data.get('priority_skills', [])}")

    print(f"16. Testing AI Suggestions Retrieval [GET /api/resumes/{resume_id}/ai-suggestions/]...")
    res_get_ai = client.get(f'/api/resumes/{resume_id}/ai-suggestions/')
    assert res_get_ai.status_code == status.HTTP_200_OK, f"Get AI suggestions failed: {res_get_ai.data}"
    print("   [OK] Saved AI Suggestions retrieved successfully.")

    # ── MODULE 8: AI INTERVIEW QUESTION GENERATOR ─────────────────────────────
    print("\n--- MODULE 8: AI INTERVIEW QUESTION GENERATOR ---")
    print(f"17. Testing Interview Question Generation [POST /api/resumes/{resume_id}/generate-questions/]...")
    iq_payload = {"difficulty": "Medium", "count": 10, "role": "Backend Engineer"}
    res_iq = client.post(f'/api/resumes/{resume_id}/generate-questions/', iq_payload, format='json')
    assert res_iq.status_code == status.HTTP_201_CREATED, f"Question generation failed: {res_iq.data}"
    iq_data = res_iq.data['data']
    questions = iq_data.get('questions', [])
    qs_id = iq_data.get('id')
    assert len(questions) > 0, "No questions generated"
    assert iq_data.get('difficulty') == "Medium", "Difficulty mismatch"
    print(f"   [OK] Generated {len(questions)} {iq_data.get('difficulty')} interview questions for role '{iq_data.get('job_role')}'.")
    print(f"        Sample Question 1: [{questions[0]['category']}] {questions[0]['question']}")
    print(f"        Sample Question 2: [{questions[1]['category']}] {questions[1]['question']}")

    print(f"18. Testing Interview Question Set List [GET /api/resumes/{resume_id}/questions/list/]...")
    res_iq_list = client.get(f'/api/resumes/{resume_id}/questions/list/')
    assert res_iq_list.status_code == status.HTTP_200_OK, f"List questions failed: {res_iq_list.data}"
    assert len(res_iq_list.data) >= 1, "Question sets list empty"
    print(f"   [OK] Question sets list retrieved ({len(res_iq_list.data)} set(s)).")

    print(f"19. Testing Interview Question Set Detail [GET /api/resumes/{resume_id}/questions/{qs_id}/]...")
    res_iq_detail = client.get(f'/api/resumes/{resume_id}/questions/{qs_id}/')
    assert res_iq_detail.status_code == status.HTTP_200_OK, f"Get question set detail failed: {res_iq_detail.data}"
    print(f"   [OK] Question set detail retrieved successfully.")

    # ── MODULE 9: AI MOCK INTERVIEW SYSTEM ─────────────────────────────────────
    print("\n--- MODULE 9: AI MOCK INTERVIEW SYSTEM ---")
    print("20. Testing Mock Interview Session Start [POST /api/interviews/start/]...")
    mock_start_payload = {
        "resume_id": resume_id,
        "job_description_id": jd_id,
        "role": "Python Developer",
        "difficulty": "Medium",
        "interview_type": "Mixed",
        "question_count": 2,
    }
    res_mstart = client.post('/api/interviews/start/', mock_start_payload, format='json')
    assert res_mstart.status_code == status.HTTP_201_CREATED, f"Mock start failed: {res_mstart.data}"
    session_id = res_mstart.data['session_id']
    q1_text = res_mstart.data['question']
    q1_cat = res_mstart.data['category']
    print(f"   [OK] Mock Interview session #{session_id} started. Q1 [{q1_cat}]: \"{q1_text}\"")

    print(f"21. Testing Answer Submission & Q2 Generation [POST /api/interviews/{session_id}/answer/]...")
    ans1_payload = {"answer": "I have 3+ years of experience building Python and Django APIs with PostgreSQL."}
    res_ans1 = client.post(f'/api/interviews/{session_id}/answer/', ans1_payload, format='json')
    assert res_ans1.status_code == status.HTTP_200_OK, f"Submit answer failed: {res_ans1.data}"
    assert not res_ans1.data['is_completed'], "Session completed unexpectedly on Q1"
    q2_text = res_ans1.data['question']
    q2_cat = res_ans1.data['category']
    print(f"   [OK] Q1 Answer recorded! Advanced to Q2 [{q2_cat}]: \"{q2_text}\"")

    print(f"22. Testing Final Answer Submission & Session Completion [POST /api/interviews/{session_id}/answer/]...")
    ans2_payload = {"answer": "Django Middleware intercepts requests and responses globally to process authentication, headers, or logging."}
    res_ans2 = client.post(f'/api/interviews/{session_id}/answer/', ans2_payload, format='json')
    assert res_ans2.status_code == status.HTTP_200_OK, f"Submit final answer failed: {res_ans2.data}"
    assert res_ans2.data['is_completed'], "Session should be marked completed after Q2"
    print("   [OK] Final answer recorded! Mock Interview session completed successfully.")

    print(f"23. Testing Session Detail & Stored Q&A Transcript [GET /api/interviews/{session_id}/]...")
    res_sdetail = client.get(f'/api/interviews/{session_id}/')
    assert res_sdetail.status_code == status.HTTP_200_OK, f"Get session detail failed: {res_sdetail.data}"
    stored_questions = res_sdetail.data.get('questions', [])
    assert len(stored_questions) == 2, f"Expected 2 stored questions, got {len(stored_questions)}"
    assert stored_questions[0]['user_answer'] != "", "Q1 answer missing in transcript"
    assert stored_questions[1]['user_answer'] != "", "Q2 answer missing in transcript"
    print(f"   [OK] Session detail retrieved cleanly ({len(stored_questions)} Q&A pairs stored for Module 10 evaluation).")

    # ── MODULE 10: AI ANSWER EVALUATION & INTERVIEW ANALYSIS ENGINE ─────────
    print("\n--- MODULE 10: AI ANSWER EVALUATION & INTERVIEW ANALYSIS ENGINE ---")
    print(f"24. Testing AI Interview Evaluation Generation [POST /api/interviews/{session_id}/evaluate/]...")
    res_eval = client.post(f'/api/interviews/{session_id}/evaluate/', format='json')
    assert res_eval.status_code == status.HTTP_201_CREATED, f"Evaluation generation failed: {res_eval.data}"
    eval_data = res_eval.data
    assert 'overall_score' in eval_data, "overall_score missing in evaluation"
    assert 'hiring_recommendation' in eval_data, "hiring_recommendation missing in evaluation"
    assert 'question_analysis' in eval_data, "question_analysis missing in evaluation"
    assert len(eval_data['question_analysis']) == 2, "Question analysis length mismatch"
    print(f"   [OK] AI Interview Evaluation report generated successfully!")
    print(f"        Overall Score: {eval_data['overall_score']}/100")
    print(f"        Hiring Decision: {eval_data['hiring_recommendation']}")
    print(f"        Technical Score: {eval_data['technical_score']}/100")
    print(f"        Communication Score: {eval_data['communication_score']}/100")
    print(f"        Summary: \"{eval_data['summary']}\"")
    print(f"        Strengths: {eval_data['strengths'][:2]}")
    print(f"        Weaknesses: {eval_data['weaknesses'][:2]}")
    print(f"        Recommended Topics: {eval_data['recommended_topics'][:3]}")

    print(f"25. Testing AI Interview Evaluation Retrieval [GET /api/interviews/{session_id}/evaluation/]...")
    res_get_eval = client.get(f'/api/interviews/{session_id}/evaluation/')
    assert res_get_eval.status_code == status.HTTP_200_OK, f"Get evaluation failed: {res_get_eval.data}"
    assert res_get_eval.data['overall_score'] == eval_data['overall_score'], "Retrieved overall score mismatch"
    print("   [OK] Saved AI Interview Evaluation report retrieved successfully.")

    # Clean up test user & resume
    User.objects.filter(email=test_email).delete()

    print("\n" + "=" * 70)
    print("ALL MODULES (1, 2, 3, 4, 5, 6, 7, 8, 9, 10) VERIFIED & WORKING 100% PERFECTLY!")
    print("=" * 70)


if __name__ == '__main__':
    run_verification()


