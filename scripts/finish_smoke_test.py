import os
import sys
import time
import requests

BASE = 'http://127.0.0.1:5000'

def test_active_job_report():
    """Fetch and validate active job report"""
    print('Fetching active job report...')
    time.sleep(2)  # Give server time to start
    try:
        r = requests.get(f"{BASE}/api/jobs/active/report")
        print(f'Report status: {r.status_code}')
        if r.status_code == 200:
            report = r.json()
            print(f'  Success: {report.get("success")}')
            print(f'  Total ranked candidates: {report.get("totals", {}).get("ranked_candidates")}')
            print(f'  Top candidates count: {len(report.get("top_candidates", []))}')
            print(f'  Bands: {report.get("bands")}')
            print(f'  Matched keywords (sample): {report.get("matched_keywords", [])[:5]}')
            print(f'  Missing keywords (sample): {report.get("missing_keywords", [])[:5]}')
        else:
            print(f'  ERROR: {r.text[:200]}')
    except Exception as e:
        print(f'  Exception: {e}')


def test_download_all_candidates():
    """Download all candidates Excel"""
    print('\nDownloading all candidates Excel...')
    try:
        r = requests.get(f"{BASE}/api/download-excel")
        print(f'Download status: {r.status_code}')
        if r.status_code == 200:
            filename = 'download_test_applicants.xlsx'
            with open(filename, 'wb') as f:
                f.write(r.content)
            print(f'  Saved to: {filename} ({len(r.content)} bytes)')
        else:
            print(f'  ERROR: {r.text[:200]}')
    except Exception as e:
        print(f'  Exception: {e}')


def cleanup_test_job():
    """Delete the test job"""
    print('\nCleaning up test job...')
    try:
        # Get active job
        r = requests.get(f"{BASE}/api/jobs/active")
        if r.status_code == 200 and r.json().get('job', {}).get('Job ID'):
            job_id = r.json()['job']['Job ID']
            print(f'  Active job ID: {job_id}')
            
            # Delete it
            r = requests.delete(f"{BASE}/api/jobs/{job_id}")
            print(f'  Delete status: {r.status_code}')
            if r.status_code == 200:
                print(f'  Test job deleted successfully')
    except Exception as e:
        print(f'  Exception: {e}')


if __name__ == '__main__':
    test_active_job_report()
    test_download_all_candidates()
    cleanup_test_job()
    print('\nAll tests complete')
