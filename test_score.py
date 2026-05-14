import json
from cv_analyzer.scoring import ScoringSystem

s = ScoringSystem()
candidate = {
	'first_name': 'Alice',
	'last_name': 'Johnson',
	'city': 'Nairobi',
	'country': 'Kenya',
	'education_level': 'Master',
	'education': [{'qualification': 'MSc Computer Science'}],
	'certifications': ['AWS Certified Solutions Architect'],
	'experience': {'years': 8},
	'experience_entries': [
		{
			'employer': 'TechCorp',
			'job_title': 'Senior Engineer',
			'achievements': ['Improved deployment time by 50%', 'Led a team of 5 engineers'],
			'responsibilities': ['Design', 'Deploy']
		},
		{
			'employer': 'WebStart',
			'job_title': 'Engineer',
			'achievements': ['Delivered feature X that increased revenue by 10%'],
			'responsibilities': ['Implement', 'Test']
		}
	],
	'skills': ['Python', 'Docker', 'AWS', 'Git', 'SQL'],
	'raw_text': 'Experienced Senior Engineer with Python, AWS, Docker, SQL, Git. Led teams and improved deployment times. Volunteered on open source.'
}

breakdown = s.get_score_breakdown(candidate)
print('Experience Quality:', s.experience_quality(candidate))
print('Education & Creds:', s.education_and_creds(candidate))
print('Skills Match:', s.skills_match(candidate))
print('\nFull breakdown:\n')
print(json.dumps(breakdown, indent=2))
