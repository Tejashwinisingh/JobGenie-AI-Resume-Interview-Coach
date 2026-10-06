"""
apps/ai_resume/prompts.py

System and User Prompts for OpenAI Resume Improvement Analysis.
"""

SYSTEM_PROMPT = """You are a professional resume reviewer and senior technical recruiter with extensive experience reviewing software engineering and technology resumes.

Provide constructive, practical, ATS-friendly suggestions.
Rules:
- Never invent experience.
- Never exaggerate skills.
- Only recommend realistic, actionable improvements.
- Never suggest lying or fabricating certifications/companies.
- Always output a valid JSON object matching the requested format precisely.
"""

USER_PROMPT_TEMPLATE = """Analyze the following candidate resume profile, ATS quality report, and job match details:

CANDIDATE RESUME DATA:
- Name: {name}
- Extracted Skills: {skills}
- Education: {education}
- Work Experience: {experience}
- Projects: {projects}
- Certifications: {certifications}

ATS QUALITY REPORT:
- Score: {ats_score}/100
- Grade: {ats_grade}
- Missing Sections: {missing_sections}
- Warnings: {ats_warnings}

JOB MATCHING CONTEXT (IF AVAILABLE):
- Matched Skills: {matched_skills}
- Missing Skills: {missing_skills}

Generate a JSON object containing EXACTLY these keys:
{{
  "summary": "Concise 1-2 sentence overall summary of the candidate's resume quality and key gaps.",
  "strengths": ["List 2-4 strong points of the candidate's resume"],
  "weaknesses": ["List 2-4 areas that need improvement"],
  "suggestions": ["List 4-6 specific, actionable, ATS-friendly suggestions for the candidate"],
  "priority_skills": ["List 3-5 priority skills the candidate should learn or highlight"],
  "improved_project_description": "An improved, impact-focused, STAR-method sample project description incorporating action verbs and measurable metrics for one of their projects."
}}
"""
