import os
import sys
import json

sys.path.append(os.path.join(os.getcwd(), 'cv_analyzer'))
from scoring import ScoringSystem
from jobs_manager import JobsManager

DATA_DIR = os.path.join('cv_analyzer', 'data')
JOBS_FILE = os.path.join(DATA_DIR, 'jobs.xlsx')

def load_active_job():
    jm = JobsManager(JOBS_FILE)
    return jm.get_active_job() or {}

def make_candidates():
    return [
        {
            'first_name': 'Clara',
            'last_name': 'Masters',
            'email': 'clara.masters@example.com',
            'skills': ['Public Speaking', 'Research'],
            'education': [{'qualification': "MSc Computer Science", 'institution': 'Uni X', 'graduation_year': '2020'}],
            'education_level': 'Master',
            'experience': {'years': 1, 'current_role': 'Research Assistant'},
            'experience_entries': [
                {'job_title': 'Research Assistant', 'employer': 'Uni X', 'achievements': ['Published 1 paper'], 'responsibilities': ['Data collection']}],
            'raw_text': 'Master degree in Computer Science, research background, limited industry automation experience.'
        },
        {
            'first_name': 'Dan',
            'last_name': 'Practitioner',
            'email': 'dan.practitioner@example.com',
            'skills': ['Python', 'CI/CD', 'Docker', 'Testing'],
            'education': [{'qualification': 'BSc Software Engineering', 'institution': 'Uni Y', 'graduation_year': '2016'}],
            'education_level': 'Degree',
            'experience': {'years': 6, 'current_role': 'Senior QA Engineer'},
            'experience_entries': [
                {'job_title': 'Senior QA Engineer', 'employer': 'Tech Co', 'achievements': ['Reduced regression time by 40%'], 'responsibilities': ['Built automation suites using pytest, Docker and CI pipelines']}],
            'raw_text': 'Practical experience building test automation, CI/CD, Docker, Python.'
        }
    ]

def run():
    sc = ScoringSystem()
    job = load_active_job()
    candidates = make_candidates()

    results = []
    for c in candidates:
        base = sc.get_score_breakdown(c)
        job_aware = sc.get_score_breakdown(c, job=job) if job else None
        results.append({'candidate': c['email'], 'base': base, 'job_aware': job_aware})

    print(json.dumps(results, indent=2))

if __name__ == '__main__':
    run()
