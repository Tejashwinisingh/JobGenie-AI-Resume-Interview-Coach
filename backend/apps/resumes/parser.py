"""
apps/resumes/parser.py

Deterministic Resume Parser Engine for Module 4.
Extracts:
  - Personal Details (Name, Email, Phone, LinkedIn, GitHub)
  - Technical Skills (Matched against predefined skills dictionary)
  - Education (Degrees, Institutions, Dates)
  - Work Experience (Roles, Companies, Dates, Bullet details)
  - Projects (Titles, Technologies, Descriptions)
  - Certifications (Names, Organizations, Dates)
"""
import re

# ─── Predefined Skills Dictionary ─────────────────────────────────────────────

SKILLS_DICTIONARY = {
    'Languages': [
        'Python', 'JavaScript', 'TypeScript', 'Java', 'C++', 'C#', 'C', 'Go', 'Rust',
        'Ruby', 'PHP', 'Swift', 'Kotlin', 'Scala', 'R', 'SQL', 'HTML', 'CSS', 'HTML5',
        'CSS3', 'Bash', 'Shell', 'PowerShell', 'Dart', 'MATLAB', 'Perl', 'Solidity'
    ],
    'Frameworks & Libraries': [
        'React', 'React.js', 'ReactJS', 'Angular', 'Vue.js', 'Vue', 'Next.js', 'Nuxt.js',
        'Django', 'Flask', 'FastAPI', 'Spring Boot', 'Spring', 'Node.js', 'Express.js',
        'Express', 'ASP.NET', 'Laravel', 'Ruby on Rails', 'Tailwind CSS', 'Tailwind',
        'Bootstrap', 'jQuery', 'Redux', 'Zustand', 'PyTorch', 'TensorFlow', 'Scikit-learn',
        'Pandas', 'NumPy', 'OpenCV', 'Keras', 'Flutter', 'React Native', 'Pygame'
    ],
    'Databases': [
        'PostgreSQL', 'Postgres', 'MySQL', 'SQLite', 'MongoDB', 'Redis', 'Elasticsearch',
        'Oracle', 'MS SQL Server', 'Cassandra', 'DynamoDB', 'Firebase', 'Supabase',
        'Neo4j', 'MariaDB', 'CockroachDB'
    ],
    'Cloud & DevOps': [
        'AWS', 'Amazon Web Services', 'Azure', 'Microsoft Azure', 'GCP', 'Google Cloud',
        'Docker', 'Kubernetes', 'K8s', 'Terraform', 'Ansible', 'Jenkins', 'CI/CD',
        'GitHub Actions', 'GitLab CI', 'NGINX', 'Apache', 'Linux', 'Unix', 'Ubuntu',
        'Serverless', 'Helm', 'Prometheus', 'Grafana'
    ],
    'Tools & Architectures': [
        'Git', 'GitHub', 'GitLab', 'Bitbucket', 'Jira', 'Postman', 'VS Code', 'Figma',
        'Webpack', 'Vite', 'Kafka', 'RabbitMQ', 'GraphQL', 'REST API', 'RESTful API',
        'Microservices', 'System Design', 'Agile', 'Scrum', 'OOP', 'Data Structures',
        'Algorithms', 'Unit Testing', 'PyTest', 'Jest', 'Cypress'
    ],
}

# Flattened set for fast lookup
ALL_KNOWN_SKILLS = {skill for cat in SKILLS_DICTIONARY.values() for skill in cat}


# ─── Parser Class ─────────────────────────────────────────────────────────────

class ResumeParser:
    """Regex & Heuristic parser for extracting structured data from resume text."""

    @classmethod
    def extract_email(cls, text):
        match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
        return match.group(0) if match else ''

    @classmethod
    def extract_phone(cls, text):
        pattern = r'(?:\+\d{1,3}[-.\s]?)?\(?\d{2,5}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}'
        match = re.search(pattern, text)
        if match:
            phone_candidate = match.group(0).strip()
            # Verify candidate has between 7 and 15 digits
            digits_count = len(re.sub(r'\D', '', phone_candidate))
            if 7 <= digits_count <= 15:
                return phone_candidate
        return ''

    @classmethod
    def extract_linkedin(cls, text):
        match = re.search(r'(?:https?://)?(?:www\.)?linkedin\.com/in/[\w-]+/?', text, re.IGNORECASE)
        if match:
            url = match.group(0).rstrip('/')
            return url if url.startswith('http') else f'https://{url}'
        return ''

    @classmethod
    def extract_github(cls, text):
        match = re.search(r'(?:https?://)?(?:www\.)?github\.com/[\w-]+/?', text, re.IGNORECASE)
        if match:
            url = match.group(0).rstrip('/')
            return url if url.startswith('http') else f'https://{url}'
        return ''

    @classmethod
    def extract_name(cls, text):
        """
        Extract candidate name from top lines of text.
        Excludes lines with email, phone, URLs, or generic headers.
        """
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        ignored_keywords = {'resume', 'curriculum', 'vitae', 'cv', 'profile', 'contact', 'summary'}

        for line in lines[:6]:
            lower_line = line.lower()
            # Skip if contains email, URL, phone digits > 5, or ignored keywords
            if '@' in line or 'http' in lower_line or 'linkedin' in lower_line or 'github' in lower_line:
                continue
            if any(kw in lower_line for kw in ignored_keywords):
                continue
            digits = len(re.sub(r'\D', '', line))
            if digits >= 5:
                continue

            # Clean name string (remove special non-letter characters)
            clean_name = re.sub(r'[^a-zA-Z\s.-]', '', line).strip()
            words = clean_name.split()
            if 1 <= len(words) <= 4:
                return clean_name.title()

        return ''

    @classmethod
    def extract_skills(cls, text):
        """Match technical skills against the predefined skills dictionary."""
        matched_skills = set()
        text_normalized = f" {text} "

        for category, skills_list in SKILLS_DICTIONARY.items():
            for skill in skills_list:
                # Boundary-aware matching for safe skill extraction
                pattern = r'(?<![a-zA-Z0-9_#+])' + re.escape(skill) + r'(?![a-zA-Z0-9_#+])'
                if re.search(pattern, text_normalized, re.IGNORECASE):
                    matched_skills.add(skill)

        return sorted(list(matched_skills))

    @classmethod
    def extract_sections(cls, text):
        """Split text into sections based on standard resume section headers."""
        header_patterns = {
            'education': r'(?:EDUCATION|ACADEMIC BACKGROUND|ACADEMIC QUALIFICATIONS|QUALIFICATIONS)',
            'experience': r'(?:WORK EXPERIENCE|PROFESSIONAL EXPERIENCE|EXPERIENCE|EMPLOYMENT HISTORY|WORK HISTORY)',
            'projects': r'(?:PROJECTS|PERSONAL PROJECTS|KEY PROJECTS|ACADEMIC PROJECTS)',
            'certifications': r'(?:CERTIFICATIONS|CERTIFICATES|LICENSES & CERTIFICATIONS|COURSES)',
            'skills': r'(?:SKILLS|TECHNICAL SKILLS|CORE COMPETENCIES|SKILLS & TECHNOLOGIES)',
        }

        # Find line index for headers
        combined_pattern = r'^(?P<header>' + '|'.join(header_patterns.values()) + r')[\s:]*$'
        lines = text.split('\n')
        section_indices = []

        for idx, line in enumerate(lines):
            stripped = line.strip().upper()
            for key, pat in header_patterns.items():
                if re.match(r'^' + pat + r'[\s:]*$', stripped):
                    section_indices.append((idx, key))
                    break

        sections = {}
        for i, (start_idx, sec_key) in enumerate(section_indices):
            end_idx = section_indices[i + 1][0] if i + 1 < len(section_indices) else len(lines)
            sec_content = "\n".join(lines[start_idx + 1:end_idx]).strip()
            sections[sec_key] = sec_content

        return sections

    @classmethod
    def parse_education(cls, education_text):
        """Parse education section into structured degree objects."""
        if not education_text:
            return []

        degree_keywords = [
            'Bachelor', 'B.S.', 'B.S', 'BS', 'B.Tech', 'BTech', 'B.E.', 'BE',
            'Master', 'M.S.', 'M.S', 'MS', 'M.Tech', 'MTech', 'Ph.D', 'PhD',
            'Associate', 'Diploma', 'High School'
        ]
        year_pattern = r'\b(19\d{2}|20\d{2})\b'

        entries = []
        blocks = [b.strip() for b in education_text.split('\n\n') if b.strip()]
        if not blocks or len(blocks) == 1:
            blocks = [b.strip() for b in education_text.split('\n') if b.strip()]

        for block in blocks:
            years = re.findall(year_pattern, block)
            date_str = " - ".join(years) if years else ''
            
            # Find degree match
            found_degree = ''
            for line in block.split('\n'):
                for deg in degree_keywords:
                    if deg.lower() in line.lower():
                        found_degree = line.strip()
                        break
                if found_degree:
                    break

            if found_degree or years or len(block) > 5:
                entries.append({
                    'degree': found_degree if found_degree else block.split('\n')[0],
                    'institution': block.replace(found_degree, '').strip() if found_degree else '',
                    'date': date_str,
                    'details': block,
                })

        return entries[:5]  # Cap at top 5 entries

    @classmethod
    def parse_experience(cls, experience_text):
        """Parse experience section into structured work entries."""
        if not experience_text:
            return []

        date_pattern = r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December)?[\s,.]*\d{4}\b'
        
        entries = []
        blocks = [b.strip() for b in experience_text.split('\n\n') if b.strip()]
        if not blocks or len(blocks) == 1:
            # Fallback to splitting by bullet lines or headers
            blocks = [b.strip() for b in experience_text.split('\n') if b.strip()]

        for block in blocks:
            lines = [l.strip() for l in block.split('\n') if l.strip()]
            if not lines:
                continue

            title_line = lines[0]
            dates = re.findall(date_pattern, block, re.IGNORECASE)
            date_str = " - ".join(dates[:2]) if dates else ''

            bullets = [l.lstrip('-•* ').strip() for l in lines[1:] if l.startswith(('-', '•', '*')) or len(l) > 10]

            entries.append({
                'title': title_line,
                'company': lines[1] if len(lines) > 1 and not lines[1].startswith(('-', '•', '*')) else '',
                'date': date_str,
                'bullets': bullets[:6],
                'raw_block': block,
            })

        return entries[:8]  # Cap at top 8 entries

    @classmethod
    def parse_projects(cls, projects_text):
        """Parse projects section into structured project objects."""
        if not projects_text:
            return []

        entries = []
        blocks = [b.strip() for b in projects_text.split('\n\n') if b.strip()]
        if not blocks or len(blocks) == 1:
            blocks = [b.strip() for b in projects_text.split('\n') if b.strip()]

        for block in blocks:
            lines = [l.strip() for l in block.split('\n') if l.strip()]
            if not lines:
                continue

            title = lines[0]
            desc = " ".join(lines[1:]) if len(lines) > 1 else title
            project_skills = [s for s in ALL_KNOWN_SKILLS if re.search(r'\b' + re.escape(s) + r'\b', block, re.IGNORECASE)]

            entries.append({
                'title': title,
                'description': desc,
                'technologies': project_skills[:8],
            })

        return entries[:6]  # Cap at top 6 projects

    @classmethod
    def parse_certifications(cls, certs_text):
        """Parse certifications section into list of certificate entries."""
        if not certs_text:
            return []

        certs = []
        lines = [l.strip().lstrip('-•* ') for l in certs_text.split('\n') if l.strip()]
        for line in lines:
            if len(line) > 3:
                certs.append({'name': line})

        return certs[:10]  # Cap at top 10 certifications

    @classmethod
    def parse_resume(cls, cleaned_text):
        """
        Main entry point for parsing cleaned resume text.
        Returns a dict of all structured fields.
        """
        if not cleaned_text:
            cleaned_text = ""

        # 1. Contact Info
        email = cls.extract_email(cleaned_text)
        phone = cls.extract_phone(cleaned_text)
        linkedin = cls.extract_linkedin(cleaned_text)
        github = cls.extract_github(cleaned_text)
        name = cls.extract_name(cleaned_text)

        # 2. Skills
        skills = cls.extract_skills(cleaned_text)

        # 3. Sections
        sections = cls.extract_sections(cleaned_text)
        education = cls.parse_education(sections.get('education', ''))
        experience = cls.parse_experience(sections.get('experience', ''))
        projects = cls.parse_projects(sections.get('projects', ''))
        certifications = cls.parse_certifications(sections.get('certifications', ''))

        return {
            'name': name,
            'email': email,
            'phone': phone,
            'linkedin': linkedin,
            'github': github,
            'skills': skills,
            'education': education,
            'experience': experience,
            'projects': projects,
            'certifications': certifications,
        }
