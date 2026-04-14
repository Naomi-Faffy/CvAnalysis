from typing import Dict, List


class ScoringSystem:
    def __init__(self, required_skills: List[str] = None):
        self.required_skills = required_skills or [
            'Python', 'JavaScript', 'SQL', 'Git', 'Communication',
            'Data Analysis', 'Problem Solving', 'Teamwork'
        ]
        self.max_scores = {
            'identity': 20,
            'address': 15,
            'education': 25,
            'experience': 20,
            'skills': 20,
        }
        self.max_total = sum(self.max_scores.values())

    def calculate_identity_score(self, candidate: Dict) -> float:
        score = 0
        max_score = self.max_scores['identity']

        age = candidate.get('age', 0) or 0
        age_dob = str(candidate.get('age_dob', '')).strip()
        if age_dob:
            score += 8
        if age:
            if 20 <= age <= 30:
                score += 8
            elif 31 <= age <= 35:
                score += 5
            else:
                score += 3

        gender = str(candidate.get('gender', '')).strip().lower()
        if gender and gender not in ['not specified', 'unknown']:
            score += 4

        if candidate.get('first_name'):
            score += 4
        if candidate.get('last_name'):
            score += 4

        return min(score, max_score)

    def calculate_address_score(self, candidate: Dict) -> float:
        score = 0
        max_score = self.max_scores['address']

        if candidate.get('city'):
            score += 7
        if candidate.get('country'):
            score += 8

        return min(score, max_score)

    def calculate_education_score(self, candidate: Dict) -> float:
        score = 0
        max_score = self.max_scores['education']

        education = candidate.get('education', [])
        level = str(candidate.get('education_level', '')).lower()

        if education:
            score += 15
            if len(education) > 1:
                score += 3

            for edu in education:
                qual = edu.get('qualification', '').lower()
                if any(key in qual for key in ['computer', 'information', 'software', 'engineering', 'data', 'science', 'technology']):
                    score += 5
                    break

        if 'phd' in level:
            score += 7
        elif 'master' in level:
            score += 6
        elif 'degree' in level:
            score += 5
        elif 'diploma' in level:
            score += 4

        if any(item.get('graduation_year') for item in education):
            score += 2

        return min(score, max_score)

    def calculate_experience_score(self, candidate: Dict) -> float:
        score = 0
        max_score = self.max_scores['experience']

        experience = candidate.get('experience', {})
        years = experience.get('years', 0)

        if years == 0:
            score += 8
        elif 1 <= years <= 2:
            score += 15
        elif 3 <= years <= 4:
            score += 20
        else:
            score += 12

        if experience.get('current_role'):
            score += 2

        return min(score, max_score)

    def calculate_skills_score(self, candidate: Dict) -> float:
        score = 0
        max_score = self.max_scores['skills']

        candidate_skills = [s.lower() for s in candidate.get('skills', [])]
        required_skills_lower = [s.lower() for s in self.required_skills]
        matched = sum(1 for skill in candidate_skills if skill in required_skills_lower)

        if matched > 0:
            score = (matched / len(self.required_skills)) * max_score

        return min(score, max_score)

    def calculate_total_score(self, candidate: Dict) -> float:
        return round(
            self.calculate_identity_score(candidate)
            + self.calculate_address_score(candidate)
            + self.calculate_education_score(candidate)
            + self.calculate_experience_score(candidate)
            + self.calculate_skills_score(candidate),
            2
        )

    def calculate_final_score(self, candidate: Dict) -> float:
        total_score = self.calculate_total_score(candidate)
        percentage = (total_score / self.max_total) * 100 if self.max_total else 0
        return round(percentage, 2)

    def get_score_breakdown(self, candidate: Dict) -> Dict:
        return {
            'identity': self.calculate_identity_score(candidate),
            'address': self.calculate_address_score(candidate),
            'education': self.calculate_education_score(candidate),
            'experience': self.calculate_experience_score(candidate),
            'skills': self.calculate_skills_score(candidate),
            'total_candidate_score': self.calculate_total_score(candidate),
            'max_score': self.max_total,
            'final_score': self.calculate_final_score(candidate)
        }
