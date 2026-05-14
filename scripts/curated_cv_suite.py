import os
import sys
import csv
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


def make_curated_candidates():
    return [
        # Master's, research heavy, low industry experience
        {'email': 'clara.masters@example.com', 'first_name':'Clara','last_name':'Masters','education_level':'Master','education':[{'qualification':'MSc Computer Science'}],'experience':{'years':1},'skills':['research','python'],'experience_entries':[{'job_title':'Research Assistant','achievements':['Published 1 paper'],'responsibilities':['Data collection']}],'raw_text':'MSc, research, limited industry automation.'},
        # Practitioner with applied automation experience
        {'email':'dan.practitioner@example.com','first_name':'Dan','last_name':'Practitioner','education_level':'Degree','education':[{'qualification':'BSc Software Engineering'}],'experience':{'years':6},'skills':['Python','CI/CD','Docker','Testing'],'experience_entries':[{'job_title':'Senior QA Engineer','achievements':['Reduced regression time by 40%'],'responsibilities':['Built automation suites using pytest, Docker and CI pipelines']}],'raw_text':'Practical experience building test automation, CI/CD, Docker, Python.'},
        # Senior with leadership and strategy
        {'email':'emma.senior@example.com','first_name':'Emma','last_name':'Senior','education_level':'Degree','experience':{'years':12},'skills':['Leadership','Strategy','Testing','Python'],'experience_entries':[{'job_title':'QA Lead','achievements':['Led team of 8, improved processes'],'responsibilities':['Define QA strategy','mentor engineers']}],'raw_text':'Senior QA leader with deep automation and leadership experience.'},
        # Junior with internship only
        {'email':'frank.junior@example.com','first_name':'Frank','last_name':'Junior','education_level':'Degree','experience':{'years':0},'skills':['Testing'],'experience_entries':[{'job_title':'Intern','achievements':[],'responsibilities':['manual testing']}],'raw_text':'Recent graduate with internship experience, looking for entry role.'},
        # Strong achievements but weak presentation
        {'email':'grace.achiever@example.com','first_name':'Grace','last_name':'Achiever','education_level':'Degree','experience':{'years':5},'skills':['Python','Testing'],'experience_entries':[{'job_title':'Engineer','achievements':['Saved $200k by automation'],'responsibilities':['built scripts']}],'raw_text':'Bulleted achievements but messy formatting and long paragraphs with few sections.'},
        # Diploma holder with practical skills
        {'email':'henry.skillful@example.com','first_name':'Henry','last_name':'Skillful','education_level':'Diploma','experience':{'years':7},'skills':['Python','Docker','CI/CD'],'experience_entries':[{'job_title':'Automation Engineer','achievements':['Implemented CI pipelines'],'responsibilities':['automation']}],'raw_text':'Hands-on automation and CI/CD experience despite diploma-level education.'},
        # Strong soft skills, volunteer background
        {'email':'irene.soft@example.com','first_name':'Irene','last_name':'Soft','education_level':'Degree','experience':{'years':4},'skills':['communication','teamwork'],'experience_entries':[{'job_title':'Coordinator','achievements':['Organized volunteer programs'],'responsibilities':['coordination']}],'raw_text':'Volunteer coordinator with strong soft skills but limited technical skills.'},
        # Poor presentation and missing contact info
        {'email':'jack.missing@example.com','first_name':'Jack','last_name':'Missing','education_level':'Unknown','experience':{'years':2},'skills':['unknown'],'experience_entries':[],'raw_text':'No clear sections, missing contact email/phone in body.'}
    ]


def run_suite():
    sc = ScoringSystem()
    job = ensure_active_job()
    candidates = make_curated_candidates()

    out_file = 'curated_cv_comparison.csv'
    headers = ['email','base_final_score','job_final_score','job_fit_score','keyword_match_score','gap_penalty','gaps']
    with open(out_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for c in candidates:
            base = sc.get_score_breakdown(c)
            job_aware = sc.get_score_breakdown(c, job=job)
            job_fit = job_aware.get('job_fit', {})
            gaps_json = json.dumps(job_fit.get('gaps'))
            writer.writerow([
                c['email'],
                base.get('final_score'),
                job_aware.get('final_score'),
                job_fit.get('job_fit_score'),
                job_fit.get('keyword_match_score'),
                job_fit.get('gap_penalty'),
                gaps_json
            ])

    print('Wrote:', out_file)

if __name__ == '__main__':
    run_suite()
