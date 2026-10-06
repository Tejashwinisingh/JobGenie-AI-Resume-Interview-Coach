"""
apps/ats/constants.py

Central configuration for the ATS Analysis Engine.
All weights, keyword dictionaries, section headings, and grade thresholds
are defined here so they can be updated without touching evaluator logic.
"""
from typing import Dict, List

# ─── Score Weights ────────────────────────────────────────────────────────────
# Total = 100
WEIGHTS: Dict[str, int] = {
    "formatting": 15,
    "contact":    10,
    "structure":  10,
    "keywords":   25,
    "skills":     15,
    "education":  10,
    "experience": 10,
    "projects":    5,
}

# ─── Grade Thresholds ─────────────────────────────────────────────────────────
GRADE_THRESHOLDS: List[tuple] = [
    (90, "A+", "Excellent"),
    (80, "A",  "Very Good"),
    (70, "B",  "Good"),
    (60, "C",  "Average"),
    (0,  "D",  "Needs Improvement"),
]

# ─── Standard ATS Section Headings ────────────────────────────────────────────
# Each entry is a list of acceptable aliases for that section.
SECTION_HEADINGS: Dict[str, List[str]] = {
    "summary": [
        "summary", "professional summary", "career summary",
        "objective", "career objective", "about me", "profile",
    ],
    "skills": [
        "skills", "technical skills", "core competencies",
        "technologies", "tech stack", "competencies", "expertise",
    ],
    "education": [
        "education", "academic background", "educational qualification",
        "qualifications", "academics",
    ],
    "experience": [
        "experience", "work experience", "professional experience",
        "employment", "employment history", "work history",
        "internship", "internships", "industrial training",
    ],
    "projects": [
        "projects", "project work", "academic projects",
        "personal projects", "key projects",
    ],
    "certifications": [
        "certifications", "certificates", "certification",
        "professional certifications", "licenses",
    ],
    "achievements": [
        "achievements", "accomplishments", "awards",
        "honors", "recognition",
    ],
}

# ─── Technical Skills Dictionary ─────────────────────────────────────────────
# Organized by category. Keywords are matched case-insensitively.
TECHNICAL_SKILLS: Dict[str, List[str]] = {
    "languages": [
        "python", "java", "javascript", "typescript", "c", "c++", "c#",
        "go", "golang", "rust", "kotlin", "swift", "scala", "ruby",
        "php", "perl", "r", "matlab", "bash", "shell", "powershell",
        "dart", "elixir", "haskell", "lua", "groovy", "vba",
    ],
    "frontend": [
        "react", "angular", "vue", "vue.js", "next.js", "nextjs",
        "nuxt", "svelte", "html", "css", "sass", "scss",
        "bootstrap", "tailwind", "tailwindcss", "material ui",
        "redux", "zustand", "webpack", "vite", "babel", "jquery",
        "gatsby", "remix", "storybook",
    ],
    "backend_frameworks": [
        "django", "flask", "fastapi", "spring", "spring boot",
        "node.js", "nodejs", "express", "express.js", "nestjs", "nest.js",
        "laravel", "rails", "ruby on rails", "asp.net", "struts",
        "hibernate", "graphql", "rest api", "restful api",
        "microservices", "grpc", "soap",
    ],
    "databases": [
        "mysql", "postgresql", "postgres", "sqlite", "oracle",
        "mongodb", "redis", "cassandra", "dynamodb", "firebase",
        "elasticsearch", "neo4j", "mariadb", "mssql", "sql server",
        "influxdb", "cockroachdb", "supabase",
    ],
    "cloud_devops": [
        "aws", "amazon web services", "azure", "gcp",
        "google cloud", "docker", "kubernetes", "k8s",
        "terraform", "ansible", "jenkins", "github actions",
        "gitlab ci", "circleci", "travis ci", "helm",
        "nginx", "apache", "linux", "unix",
    ],
    "data_ml": [
        "machine learning", "deep learning", "neural network",
        "tensorflow", "pytorch", "keras", "scikit-learn", "sklearn",
        "pandas", "numpy", "matplotlib", "seaborn", "spark",
        "hadoop", "airflow", "kafka", "rabbitmq", "celery",
        "data science", "nlp", "computer vision", "llm",
    ],
    "tools": [
        "git", "github", "gitlab", "bitbucket", "jira",
        "confluence", "postman", "swagger", "sonarqube",
        "maven", "gradle", "npm", "yarn", "pip",
        "pytest", "junit", "mockito", "selenium", "cypress",
        "figma", "vs code", "intellij", "eclipse", "android studio",
    ],
    "mobile": [
        "android", "ios", "react native", "flutter",
        "swift", "kotlin", "xamarin",
    ],
    "security": [
        "oauth", "jwt", "ssl", "tls", "https",
        "encryption", "hashing", "penetration testing",
    ],
    "methodologies": [
        "agile", "scrum", "kanban", "devops", "ci/cd",
        "tdd", "bdd", "solid", "design patterns", "oop",
        "object oriented", "functional programming", "mvc",
    ],
}

# Flat list of all keywords for quick lookups
ALL_KEYWORDS: List[str] = [
    kw
    for category_list in TECHNICAL_SKILLS.values()
    for kw in category_list
]

# ─── Formatting Quality Thresholds ───────────────────────────────────────────
MIN_TEXT_LENGTH: int = 100        # Characters — below this is considered blank
MAX_WHITESPACE_RATIO: float = 0.4  # Fraction of whitespace is excessive

# ─── Keyword Density Config ───────────────────────────────────────────────────
# If a keyword appears more than this ratio of the total word count → stuffing
KEYWORD_STUFFING_THRESHOLD: float = 0.03  # 3% of total words per keyword
