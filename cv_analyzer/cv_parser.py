import re
from datetime import datetime
from typing import Dict, List, Tuple

import pdfplumber
from docx import Document
import spacy

class CVParser:
    def __init__(self):
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except Exception:
            print("Warning: spacy model not loaded. Install with: python -m spacy download en_core_web_sm")
            self.nlp = None
        
        self.common_skills = [
            'Python', 'Java', 'JavaScript', 'C++', 'C#', 'SQL', 'HTML', 'CSS', 'React', 'Angular',
            'Vue', 'Node.js', 'Express', 'Django', 'Flask', 'Spring', 'AWS', 'Azure', 'GCP',
            'Docker', 'Kubernetes', 'Git', 'Linux', 'Windows', 'Excel', 'Power BI', 'Tableau',
            'Machine Learning', 'Data Analysis', 'Statistics', 'Communication', 'Leadership',
            'Project Management', 'Agile', 'Scrum', 'MongoDB', 'PostgreSQL', 'MySQL', 'API',
            'REST', 'GraphQL', 'CI/CD', 'Jenkins', 'GitHub', 'Gitlab', 'Bitbucket', 'Jira',
            'Salesforce', 'SAP', 'ERP', 'CRM', 'Finance', 'Accounting', 'Marketing', 'Sales'
        ]
        self.skill_aliases = {
            'js': 'JavaScript',
            'javascript': 'JavaScript',
            'py': 'Python',
            'node': 'Node.js',
            'nodejs': 'Node.js',
            'postgres': 'PostgreSQL',
            'ml': 'Machine Learning',
            'ai': 'Machine Learning',
            'powerbi': 'Power BI',
            'gitlab': 'Gitlab'
        }
        self.countries = [
            'USA', 'United States', 'UK', 'United Kingdom', 'Canada', 'India', 'Australia',
            'Germany', 'France', 'Japan', 'Singapore', 'UAE', 'Netherlands', 'Brazil',
            'South Africa', 'Kenya', 'Nigeria', 'Ghana', 'Zimbabwe', 'Zambia', 'Botswana'
        ]
        self.region_country_map = {
            'harare': 'Zimbabwe',
            'bulawayo': 'Zimbabwe',
            'mutare': 'Zimbabwe',
            'gaborone': 'Botswana',
            'lusaka': 'Zambia',
            'nairobi': 'Kenya',
            'lagos': 'Nigeria',
            'accra': 'Ghana',
            'johannesburg': 'South Africa',
            'cape town': 'South Africa',
            'pretoria': 'South Africa'
        }
        self.institution_keywords = [
            'university', 'college', 'polytechnic', 'institute', 'school of', 'academy'
        ]

    def extract_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file"""
        text = ""
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() or ""
        except Exception as e:
            print(f"Error extracting PDF: {e}")
        return text

    def extract_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX file"""
        text = ""
        try:
            doc = Document(file_path)
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
        except Exception as e:
            print(f"Error extracting DOCX: {e}")
        return text

    def _clean_text(self, text: str) -> str:
        normalized = re.sub(r'\r', '\n', text or "")
        normalized = re.sub(r'\n{3,}', '\n\n', normalized)
        normalized = re.sub(r'\t+', ' ', normalized)
        return normalized.strip()

    def extract_email(self, text: str) -> str:
        """Extract email address"""
        pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        matches = re.findall(pattern, text)
        return matches[0].lower() if matches else ""

    def extract_phone(self, text: str) -> str:
        """Extract phone number"""
        patterns = [
            r'(?:\+\d{1,3}[-.\s]?)?\(?(?:\d{2,4})\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}',
            r'\+\d{9,15}',
            r'\b\d{10,13}\b'
        ]
        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                phone = re.sub(r'\s+', ' ', matches[0]).strip()
                return phone
        return ""

    def extract_names(self, text: str) -> Tuple[str, str]:
        """Extract first and last names"""
        first_name = ""
        last_name = ""
        
        lines = text.split('\n')
        for line in lines[:5]:  # Check first 5 lines
            line = line.strip()
            if "@" in line or any(ch.isdigit() for ch in line):
                continue
            if len(line) > 3 and len(line.split()) >= 2:
                words = line.split()
                first_name = words[0]
                last_name = words[1]
                break

        if self.nlp and not first_name:
            doc = self.nlp(text[:1500])
            for ent in doc.ents:
                if ent.label_ == "PERSON":
                    parts = ent.text.split()
                    if len(parts) >= 2:
                        first_name = parts[0]
                        last_name = parts[1]
                        break
        
        # Clean up
        first_name = re.sub(r'[^a-zA-Z]', '', first_name).strip()
        last_name = re.sub(r'[^a-zA-Z]', '', last_name).strip()
        
        return first_name, last_name

    def extract_gender(self, text: str) -> str:
        """Infer gender from pronouns or titles"""
        text_lower = text.lower()
        
        female_indicators = ['she/her', 'pronouns: she', 'mrs.', 'ms.', 'miss', 'chairwoman', 'female']
        male_indicators = ['he/him', 'pronouns: he', 'mr.', 'chairman', 'male']
        
        for indicator in female_indicators:
            if indicator in text_lower:
                return "Female"
        
        for indicator in male_indicators:
            if indicator in text_lower:
                return "Male"
        
        return "Not specified"

    def extract_location(self, text: str) -> Tuple[str, str]:
        """Extract city and country"""
        city = ""
        country = ""

        text_upper = text.upper()
        for country_name in self.countries:
            if country_name.upper() in text_upper:
                country = country_name
                break

        lines = text.split('\n')
        for line in lines[:20]:
            words = line.split(',')
            if len(words) > 1 and country and country.lower() in words[-1].lower():
                city = words[0].strip()
                break

        if self.nlp and (not city or not country):
            doc = self.nlp(text[:2000])
            gpe_entities = [ent.text for ent in doc.ents if ent.label_ in ["GPE", "LOC"]]
            if gpe_entities and not city:
                city = gpe_entities[0]

        if not country:
            lowered = text.lower()
            for region, mapped_country in self.region_country_map.items():
                if region in lowered:
                    country = mapped_country
                    if not city:
                        city = region.title()
                    break
        
        return city, country

    def extract_institutions(self, text: str) -> List[str]:
        institutions = []
        lines = [line.strip() for line in text.split('\n') if line.strip()]

        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in self.institution_keywords):
                cleaned = re.sub(r'\s+', ' ', line).strip(' -:;')
                if len(cleaned) > 4 and cleaned not in institutions:
                    institutions.append(cleaned)

        if self.nlp and not institutions:
            doc = self.nlp(text[:3000])
            orgs = [ent.text.strip() for ent in doc.ents if ent.label_ == "ORG"]
            for org in orgs:
                if any(keyword in org.lower() for keyword in self.institution_keywords):
                    if org not in institutions:
                        institutions.append(org)

        return institutions[:5]

    def extract_education(self, text: str) -> List[Dict]:
        """Extract education details"""
        education = []
        
        degree_keywords = ['bachelor', 'master', 'phd', 'diploma', 'bsc', 'msc', 'btech', 
                          'mtech', 'degree', 'graduation', 'graduated', 'b.a', 'b.s', 'b.e']
        
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if any(keyword in line.lower() for keyword in degree_keywords):
                year_match = re.search(r'(19|20)\d{2}', line)
                next_line = lines[i+1].strip() if i+1 < len(lines) else ""
                institution = ""
                if any(keyword in next_line.lower() for keyword in self.institution_keywords):
                    institution = next_line
                education.append({
                    'qualification': line.strip(),
                    'details': next_line,
                    'institution': institution,
                    'graduation_year': year_match.group(0) if year_match else ""
                })

        if not education:
            for institution in self.extract_institutions(text):
                education.append({
                    'qualification': institution,
                    'details': 'Institution detected from CV text',
                    'institution': institution,
                    'graduation_year': ''
                })
        
        return education

    def extract_experience(self, text: str) -> Dict:
        """Extract experience information"""
        experience = {
            'years': 0,
            'current_role': "",
            'previous_roles': []
        }
        
        # Look for years of experience
        year_patterns = [
            r'(\d+)\s*(?:\+)?\s*years?',
            r'years?[\s:]+(\d+)',
        ]
        
        for pattern in year_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    experience['years'] = int(matches[0])
                    break
                except Exception:
                    pass
        
        # Look for job titles
        job_keywords = ['developer', 'engineer', 'manager', 'analyst', 'designer', 
                       'consultant', 'architect', 'lead', 'senior', 'junior']
        
        lines = text.split('\n')
        for line in lines:
            if any(keyword in line.lower() for keyword in job_keywords):
                if not experience['current_role']:
                    experience['current_role'] = line.strip()
                else:
                    experience['previous_roles'].append(line.strip())
        
        return experience

    def _normalize_skill(self, skill: str) -> str:
        compact = skill.strip().lower().replace(' ', '')
        if compact in self.skill_aliases:
            return self.skill_aliases[compact]
        return skill

    def extract_skills(self, text: str) -> List[str]:
        """Extract skills from CV"""
        found_skills = set()
        text_lower = text.lower()
        
        for skill in self.common_skills:
            if skill.lower() in text_lower:
                found_skills.add(self._normalize_skill(skill))

        raw_tokens = re.findall(r'\b[a-zA-Z][a-zA-Z+.#]{1,25}\b', text)
        for token in raw_tokens:
            norm = self._normalize_skill(token)
            if norm in self.common_skills:
                found_skills.add(norm)

        return sorted(found_skills)

    def extract_age_or_dob(self, text: str) -> str:
        """Extract age or date of birth"""
        date_patterns = [
            r'(\d{1,2}[-/]\d{1,2}[-/]\d{4})',
            r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}',
            r'age[\s:]+(\d{1,3})',
            r'born[\s:]+(\d{4})'
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return matches[0]
        
        return ""

    def _calculate_age(self, age_or_dob: str) -> int:
        if not age_or_dob:
            return 0
        if age_or_dob.isdigit() and len(age_or_dob) <= 2:
            age = int(age_or_dob)
            return age if 14 <= age <= 80 else 0

        for fmt in ["%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y", "%m-%d-%Y", "%B %d %Y", "%B %d, %Y"]:
            try:
                dob = datetime.strptime(age_or_dob, fmt)
                today = datetime.today()
                return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            except ValueError:
                continue
        return 0

    def infer_education_level(self, education: List[Dict]) -> str:
        text = " ".join(item.get('qualification', '').lower() for item in education)
        if any(k in text for k in ['phd', 'doctorate']):
            return 'PhD'
        if any(k in text for k in ['master', 'msc', 'mba', 'mtech']):
            return 'Masters'
        if any(k in text for k in ['bachelor', 'bsc', 'ba', 'btech', 'degree']):
            return 'Degree'
        if any(k in text for k in ['diploma', 'certificate']):
            return 'Diploma/Certificate'
        return 'Unknown'

    def parse_cv(self, file_path: str) -> Dict:
        """Parse complete CV and extract all information"""
        if file_path.lower().endswith('.pdf'):
            text = self.extract_from_pdf(file_path)
        elif file_path.lower().endswith('.docx'):
            text = self.extract_from_docx(file_path)
        else:
            return {}

        text = self._clean_text(text)
        
        first_name, last_name = self.extract_names(text)
        email = self.extract_email(text)
        phone = self.extract_phone(text)
        gender = self.extract_gender(text)
        city, country = self.extract_location(text)
        age_dob = self.extract_age_or_dob(text)
        age = self._calculate_age(str(age_dob))
        education = self.extract_education(text)
        education_level = self.infer_education_level(education)
        experience = self.extract_experience(text)
        skills = self.extract_skills(text)
        
        return {
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'phone': phone,
            'gender': gender,
            'city': city,
            'country': country,
            'age_dob': age_dob,
            'age': age,
            'education': education,
            'education_level': education_level,
            'experience': experience,
            'skills': skills,
            'raw_text': text
        }
