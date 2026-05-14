import os
import sys
import json

sys.path.append(os.path.join(os.getcwd(), 'cv_analyzer'))
from scoring import ScoringSystem
from jobs_manager import JobsManager

DATA_DIR = os.path.join('cv_analyzer', 'data')
JOBS_FILE = os.path.join(DATA_DIR, 'jobs.xlsx')


def ensure_active_job():
    jm = JobsManager(JOBS_FILE)
    job = jm.get_active_job() or {}
    if not job.get('Job ID'):
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
        result = jm.add_job(payload)
        if result.get('success'):
            jm.set_active_job(result['job']['Job ID'])
            job = result['job']
    return job


def run_tests():
    sc = ScoringSystem()
    job = ensure_active_job()

    # Candidate A: Master's with low experience
    clara = {'email':'clara.masters@example.com','education_level':'Master','experience':{'years':1},'skills':['research'],'raw_text':'MSc, research, limited industry automation.'}
    # Candidate B: Practitioner
    dan = {'email':'dan.practitioner@example.com','education_level':'Degree','experience':{'years':6},'skills':['python','ci/cd','docker','testing'],'raw_text':'Practical automation experience with Python and CI/CD.'}

    base_clara = sc.get_score_breakdown(clara)
    job_clara = sc.get_score_breakdown(clara, job=job)
    base_dan = sc.get_score_breakdown(dan)
    job_dan = sc.get_score_breakdown(dan, job=job)

    # Assertions
    failures = []
    if not (job_dan.get('job_fit', {}).get('job_fit_score',0) > job_clara.get('job_fit', {}).get('job_fit_score',0)):
        failures.append('Expected practitioner job_fit > master_job_fit')

    # Clara should have an experience-related gap when job expects mid/senior
    gaps_clara = job_clara.get('job_fit', {}).get('gaps', [])
    if not any(g.get('type','').startswith('Experience') or g.get('severity')=='Critical' for g in gaps_clara):
        failures.append('Expected Clara to show experience gap or critical severity')

    if failures:
        print('TESTS FAILED:')
        for f in failures:
            print(' -', f)
        sys.exit(2)

    print('All unit-like checks passed')

if __name__ == '__main__':
    run_tests()
