import os
import sys
import time
import requests

# Ensure we can import local modules
sys.path.append(os.path.join(os.getcwd(), 'cv_analyzer'))
from excel_manager import ExcelManager
from scoring import ScoringSystem

BASE = 'http://127.0.0.1:5000'

def create_job():
    payload = {
        'Job Title': 'Test Automation Engineer',
        'Department / Category': 'Engineering',
        'Job Type': 'Full-time',
        'Work Mode': 'Remote',
        'Location': 'Remote',
        'Job Description': 'Automated testing and CI pipelines',
        'Key Responsibilities': 'Write tests, maintain CI, automate flows',
        'Requirements / Qualifications': 'Python, testing, CI/CD, automation',
        'Experience Level': 'Mid',
        'Application Deadline': '2026-12-31'
    }
    r = requests.post(f"{BASE}/api/jobs", json=payload)
    print('Create job status:', r.status_code)
    try:
        print(r.json())
    except Exception:
        print(r.text)
    if r.status_code in (200, 201) and r.json().get('job'):
        return r.json()['job'].get('Job ID')
    return None


def add_sample_candidates():
    em = ExcelManager(os.path.join('cv_analyzer', 'data', 'applicants.xlsx'))
    sc = ScoringSystem()

    candidates = [
        {
            'first_name': 'Alice',
            'last_name': 'Tester',
            'email': 'alice.tester@example.com',
            'phone': '+10000000001',
            'skills': ['Python', 'Git', 'Docker'],
            'education': [{'qualification': 'BSc Computer Science', 'institution': 'Uni A', 'graduation_year': '2018'}],
            'education_level': 'Degree',
            'experience': {'years': 4, 'current_role': 'QA Engineer'},
            'raw_text': 'Alice has worked on automation with Python, pytest and CI pipelines.'
        },
        {
            'first_name': 'Bob',
            'last_name': 'Developer',
            'email': 'bob.dev@example.com',
            'phone': '+10000000002',
            'skills': ['JavaScript', 'React'],
            'education': [{'qualification': 'MSc Software Engineering', 'institution': 'Uni B', 'graduation_year': '2020'}],
            'education_level': 'Master',
            'experience': {'years': 2, 'current_role': 'Frontend Developer'},
            'raw_text': 'Bob focuses on front-end development using React and JS.'
        }
    ]

    for c in candidates:
        if em.candidate_exists(c['email']):
            print('Candidate exists, skipping:', c['email'])
            continue
        scores = sc.get_score_breakdown(c)
        added = em.add_candidate(c, scores, file_name=f"{c['email']}.txt", job_assignment={})
        print('Added', c['email'], '=>', added)


if __name__ == '__main__':
    print('Debug storage before:')
    try:
        r = requests.get(f"{BASE}/api/debug/storage")
        print(r.status_code, r.json())
    except Exception as e:
        print('Could not reach server:', e)
        sys.exit(1)

    job_id = create_job()
    if not job_id:
        print('Failed to create job; aborting')
        sys.exit(1)
    print('Created job id:', job_id)

    add_sample_candidates()

    print('Activating job...')
    r = requests.post(f"{BASE}/api/jobs/{job_id}/activate")
    print('Activate status:', r.status_code)
    try:
        print(r.json())
    except Exception:
        print(r.text)

    time.sleep(1)

    print('Fetching active job report...')
    r = requests.get(f"{BASE}/api/jobs/active/report")
    print('Report status:', r.status_code)
    try:
        report = r.json()
        print('Report totals:', report.get('totals'))
        print('Top candidates (count):', len(report.get('top_candidates', [])))
    except Exception as e:
        print('Could not parse report:', e, r.text)

    print('Fetching active job matches...')
    r = requests.get(f"{BASE}/api/jobs/active/matches")
    print('Matches status:', r.status_code)
    try:
        j = r.json()
        print('Matches total:', j.get('total'))
        print('Sample:', j.get('candidates', [])[:3])
    except Exception as e:
        print('Could not parse matches:', e, r.text)

    print('Done')
