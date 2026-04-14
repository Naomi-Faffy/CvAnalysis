import os
import uuid
from typing import Dict, List

import pandas as pd


class ExcelManager:
    def __init__(self, excel_path: str = "data/applicants.xlsx"):
        self.excel_path = excel_path
        self.skill_columns = [
            'Python', 'JavaScript', 'SQL', 'Git', 'Java', 'C++', 'HTML', 'CSS',
            'React', 'Node.js', 'Django', 'Flask', 'Docker', 'AWS', 'Azure',
            'Communication', 'Leadership', 'Project Management', 'Data Analysis', 'Machine Learning'
        ]
        self.ensure_file_exists()

    def get_columns(self) -> List[str]:
        return [
            'Applicant ID',
            'First Name',
            'Last Name',
            'Email',
            'Phone',
            'Gender',
            'Age/DOB',
            'Age',
            'City',
            'Country',
            'Education',
            'Education Level',
            'Years of Experience',
            'Current Role',
            'Skills',
            *self.skill_columns,
            'Identity Score',
            'Address Score',
            'Education Score',
            'Experience Score',
            'Skills Score',
            'Total Candidate Score',
            'Max Score',
            'Final Score (%)',
            'Upload Date',
            'CV File Name'
        ]

    def ensure_file_exists(self):
        os.makedirs(os.path.dirname(self.excel_path), exist_ok=True)
        if not os.path.exists(self.excel_path):
            df = pd.DataFrame(columns=self.get_columns())
            df.to_excel(self.excel_path, index=False, sheet_name='Applicants')
            return

        df = pd.read_excel(self.excel_path)
        required = self.get_columns()
        changed = False
        for col in required:
            if col not in df.columns:
                df[col] = 0 if col in self.skill_columns else ""
                changed = True
        if changed:
            df = df[required]
            df.to_excel(self.excel_path, index=False, sheet_name='Applicants')

    def candidate_exists(self, email: str) -> bool:
        try:
            if not email:
                return False
            df = pd.read_excel(self.excel_path)
            if 'Email' not in df.columns:
                return False
            normalized_emails = df['Email'].fillna('').astype(str).str.lower().str.strip().values
            return email.lower().strip() in normalized_emails
        except Exception:
            return False

    def _new_candidate_row(self, candidate_data: Dict, scores: Dict, file_name: str = "") -> Dict:
        skills = candidate_data.get('skills', []) or []
        skills_set = {skill.strip().lower() for skill in skills}
        education_items = candidate_data.get('education', []) or []
        education_str = "; ".join(item.get('qualification', '').strip() for item in education_items if item.get('qualification'))

        row = {
            'Applicant ID': f"APP-{str(uuid.uuid4())[:8].upper()}",
            'First Name': candidate_data.get('first_name', ''),
            'Last Name': candidate_data.get('last_name', ''),
            'Email': str(candidate_data.get('email', '')).strip().lower(),
            'Phone': candidate_data.get('phone', ''),
            'Gender': candidate_data.get('gender', 'Not specified'),
            'Age/DOB': candidate_data.get('age_dob', ''),
            'Age': candidate_data.get('age', 0) or 0,
            'City': candidate_data.get('city', ''),
            'Country': candidate_data.get('country', ''),
            'Education': education_str,
            'Education Level': candidate_data.get('education_level', 'Unknown'),
            'Years of Experience': candidate_data.get('experience', {}).get('years', 0),
            'Current Role': candidate_data.get('experience', {}).get('current_role', ''),
            'Skills': ", ".join(skills),
            'Identity Score': scores.get('identity', 0),
            'Address Score': scores.get('address', 0),
            'Education Score': scores.get('education', 0),
            'Experience Score': scores.get('experience', 0),
            'Skills Score': scores.get('skills', 0),
            'Total Candidate Score': scores.get('total_candidate_score', 0),
            'Max Score': scores.get('max_score', 0),
            'Final Score (%)': scores.get('final_score', 0),
            'Upload Date': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
            'CV File Name': file_name,
        }

        for skill_col in self.skill_columns:
            row[skill_col] = 1 if skill_col.lower() in skills_set else 0

        return row

    def add_candidate(self, candidate_data: Dict, scores: Dict, file_name: str = "") -> bool:
        try:
            df = pd.read_excel(self.excel_path)
            email = str(candidate_data.get('email', '')).strip().lower()

            if email and self.candidate_exists(email):
                return False

            new_row = self._new_candidate_row(candidate_data, scores, file_name)
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            df = df[self.get_columns()]
            df.to_excel(self.excel_path, index=False, sheet_name='Applicants')
            return True
        except Exception as e:
            print(f"Error adding candidate: {e}")
            return False

    def get_all_candidates(self) -> List[Dict]:
        try:
            df = pd.read_excel(self.excel_path)
            return df.sort_values('Final Score (%)', ascending=False).to_dict('records')
        except Exception:
            return []

    def get_top_candidates(self, limit: int = 10) -> List[Dict]:
        try:
            df = pd.read_excel(self.excel_path)
            if df.empty:
                return []
            return df.sort_values('Final Score (%)', ascending=False).head(limit).to_dict('records')
        except Exception:
            return []

    def _score_distribution(self, df: pd.DataFrame) -> Dict:
        if 'Final Score (%)' not in df.columns:
            return {}
        return {
            '90-100%': int((df['Final Score (%)'] >= 90).sum()),
            '80-89%': int(((df['Final Score (%)'] >= 80) & (df['Final Score (%)'] < 90)).sum()),
            '70-79%': int(((df['Final Score (%)'] >= 70) & (df['Final Score (%)'] < 80)).sum()),
            '60-69%': int(((df['Final Score (%)'] >= 60) & (df['Final Score (%)'] < 70)).sum()),
            'Below 60%': int((df['Final Score (%)'] < 60).sum())
        }

    def _skills_frequency(self, df: pd.DataFrame) -> Dict:
        freq = {}
        for skill in self.skill_columns:
            if skill in df.columns:
                freq[skill] = int(df[skill].fillna(0).astype(int).sum())
        freq = {k: v for k, v in freq.items() if v > 0}
        return dict(sorted(freq.items(), key=lambda item: item[1], reverse=True))

    def get_statistics(self) -> Dict:
        try:
            df = pd.read_excel(self.excel_path)
            if df.empty:
                return {
                    'total_applicants': 0,
                    'average_score': 0,
                    'gender_distribution': {},
                    'location_distribution': {},
                    'city_distribution': {},
                    'education_distribution': {},
                    'experience_distribution': {},
                    'score_distribution': {},
                    'skills_frequency': {}
                }

            stats = {
                'total_applicants': len(df),
                'average_score': round(df['Final Score (%)'].mean(), 2) if 'Final Score (%)' in df.columns else 0,
                'gender_distribution': df['Gender'].fillna('Not specified').value_counts().to_dict() if 'Gender' in df.columns else {},
                'location_distribution': df['Country'].fillna('Unknown').value_counts().to_dict() if 'Country' in df.columns else {},
                'city_distribution': df['City'].fillna('Unknown').value_counts().to_dict() if 'City' in df.columns else {},
                'education_distribution': df['Education Level'].fillna('Unknown').value_counts().to_dict() if 'Education Level' in df.columns else {},
                'experience_distribution': df['Years of Experience'].fillna(0).astype(int).value_counts().sort_index().to_dict() if 'Years of Experience' in df.columns else {},
                'score_distribution': self._score_distribution(df),
                'skills_frequency': self._skills_frequency(df)
            }
            return stats
        except Exception as e:
            print(f"Error getting statistics: {e}")
            return {}

    def filter_candidates(self, filters: Dict) -> List[Dict]:
        try:
            df = pd.read_excel(self.excel_path)

            if 'min_score' in filters:
                df = df[df['Final Score (%)'] >= filters['min_score']]
            if 'max_score' in filters:
                df = df[df['Final Score (%)'] <= filters['max_score']]
            if 'gender' in filters:
                df = df[df['Gender'].fillna('').str.lower() == str(filters['gender']).lower()]
            if 'country' in filters:
                df = df[df['Country'].fillna('').str.contains(str(filters['country']), case=False, na=False)]
            if 'city' in filters:
                df = df[df['City'].fillna('').str.contains(str(filters['city']), case=False, na=False)]
            if 'education_level' in filters:
                df = df[df['Education Level'].fillna('').str.contains(str(filters['education_level']), case=False, na=False)]
            if 'min_experience' in filters:
                df = df[df['Years of Experience'].fillna(0).astype(float) >= float(filters['min_experience'])]
            if 'skill' in filters:
                skill_value = str(filters['skill']).strip().lower()
                matching_skill_cols = [col for col in self.skill_columns if col.lower() == skill_value]
                if matching_skill_cols:
                    col = matching_skill_cols[0]
                    df = df[df[col].fillna(0).astype(int) == 1]
                else:
                    df = df[df['Skills'].fillna('').str.contains(skill_value, case=False, na=False)]
            if 'search' in filters:
                query = str(filters['search'])
                df = df[
                    df['First Name'].fillna('').str.contains(query, case=False, na=False)
                    | df['Last Name'].fillna('').str.contains(query, case=False, na=False)
                    | df['Email'].fillna('').str.contains(query, case=False, na=False)
                ]

            return df.sort_values('Final Score (%)', ascending=False).to_dict('records')
        except Exception as e:
            print(f"Error filtering candidates: {e}")
            return []

    def export_to_excel(self, data: List[Dict], filename: str) -> bool:
        try:
            if not data:
                return False
            os.makedirs("data", exist_ok=True)
            df = pd.DataFrame(data)
            path = os.path.join("data", f"{filename}.xlsx")
            df.to_excel(path, index=False)
            return True
        except Exception as e:
            print(f"Error exporting to Excel: {e}")
            return False

    def delete_candidate(self, email: str) -> bool:
        try:
            normalized_email = str(email).strip().lower()
            df = pd.read_excel(self.excel_path)
            df = df[df['Email'].fillna('').str.lower() != normalized_email]
            df.to_excel(self.excel_path, index=False, sheet_name='Applicants')
            return True
        except Exception as e:
            print(f"Error deleting candidate: {e}")
            return False

    def get_candidate_by_email(self, email: str) -> Dict:
        try:
            normalized_email = str(email).strip().lower()
            df = pd.read_excel(self.excel_path)
            result = df[df['Email'].fillna('').str.lower() == normalized_email]
            if not result.empty:
                return result.iloc[0].to_dict()
            return {}
        except Exception:
            return {}
