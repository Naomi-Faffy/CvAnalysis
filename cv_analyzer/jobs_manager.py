import os
import uuid
from datetime import datetime
from typing import Dict, List

import pandas as pd


class JobsManager:
    def __init__(self, excel_path: str = "data/jobs.xlsx"):
        self.excel_path = excel_path
        self.ensure_file_exists()

    def get_columns(self) -> List[str]:
        return [
            'Job ID',
            'Job Title',
            'Department / Category',
            'Job Type',
            'Work Mode',
            'Location',
            'Job Description',
            'Key Responsibilities',
            'Requirements / Qualifications',
            'Experience Level',
            'Application Deadline',
            'Post Date'
        ]

    def ensure_file_exists(self):
        os.makedirs(os.path.dirname(self.excel_path), exist_ok=True)
        if not os.path.exists(self.excel_path):
            df = pd.DataFrame(columns=self.get_columns())
            df.to_excel(self.excel_path, index=False, sheet_name='Jobs')
            return

        df = pd.read_excel(self.excel_path)
        required = self.get_columns()
        changed = False
        for col in required:
            if col not in df.columns:
                df[col] = ''
                changed = True
        if changed:
            df = df[required]
            df.to_excel(self.excel_path, index=False, sheet_name='Jobs')

    def _normalize_text(self, value: str) -> str:
        return str(value or '').strip()

    def add_job(self, job_data: Dict) -> Dict:
        try:
            df = pd.read_excel(self.excel_path)
            job_id = f"JOB-{str(uuid.uuid4())[:8].upper()}"
            post_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            deadline = self._normalize_text(job_data.get('Application Deadline', ''))
            new_row = {
                'Job ID': job_id,
                'Job Title': self._normalize_text(job_data.get('Job Title', '')),
                'Department / Category': self._normalize_text(job_data.get('Department / Category', '')),
                'Job Type': self._normalize_text(job_data.get('Job Type', '')),
                'Work Mode': self._normalize_text(job_data.get('Work Mode', '')),
                'Location': self._normalize_text(job_data.get('Location', '')),
                'Job Description': self._normalize_text(job_data.get('Job Description', '')),
                'Key Responsibilities': self._normalize_text(job_data.get('Key Responsibilities', '')),
                'Requirements / Qualifications': self._normalize_text(job_data.get('Requirements / Qualifications', '')),
                'Experience Level': self._normalize_text(job_data.get('Experience Level', '')),
                'Application Deadline': deadline,
                'Post Date': post_date,
            }

            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            df = df[self.get_columns()]
            df.to_excel(self.excel_path, index=False, sheet_name='Jobs')
            return {'success': True, 'job': new_row}
        except Exception as e:
            print(f"Error adding job: {e}")
            return {'success': False, 'error': str(e)}

    def get_all_jobs(self) -> List[Dict]:
        try:
            df = pd.read_excel(self.excel_path)
            if df.empty:
                return []
            df['Post Date'] = pd.to_datetime(df['Post Date'], errors='coerce')
            df = df.sort_values('Post Date', ascending=False, na_position='last')
            return df.fillna('').to_dict('records')
        except Exception:
            return []

    def get_job_by_id(self, job_id: str) -> Dict:
        try:
            df = pd.read_excel(self.excel_path)
            result = df[df['Job ID'].fillna('').astype(str) == str(job_id)]
            if not result.empty:
                return result.iloc[0].to_dict()
            return {}
        except Exception:
            return {}