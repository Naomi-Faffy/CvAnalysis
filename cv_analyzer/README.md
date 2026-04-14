# Graduate Trainee CV Analyzer (Excel-Only)

A lightweight web application for managing and analyzing Graduate Trainee applications.

- Upload CV files in PDF and DOCX (single or batch)
- Extract candidate identity, contact, location, education, experience, and skills
- Score candidates with weighted scoring logic
- Store all records in `data/applicants.xlsx` (no database)
- Visual dashboard with charts and top candidates
- Search, filter, delete, and export candidate data
- One-click filtered export download from the browser

## Tech Stack

- Backend: Flask
- Parsing: pdfplumber, python-docx, regex, spaCy (optional model)
- Excel storage: pandas + openpyxl
- Frontend: HTML, CSS, JavaScript + Chart.js

## Project Structure

```text
cv_analyzer/
  app.py
  cv_parser.py
  excel_manager.py
  scoring.py
  requirements.txt
  README.md
  data/
    applicants.xlsx (auto-created)
  uploads/
  static/
    css/
      style.css
    js/
      app.js
  templates/
    index.html
```

## Setup

1. Open a terminal in `cv_analyzer`.
2. Create and activate a virtual environment.
3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. (Recommended) Install spaCy English model for better name/location extraction:

```bash
python -m spacy download en_core_web_sm
```

5. Run the application:

```bash
python app.py
```

6. Open your browser:

```text
http://127.0.0.1:5000
```

## Data Storage Rules

- Uploaded CVs are stored in `uploads/`
- Applicant records are stored in `data/applicants.xlsx`
- Duplicate candidates are prevented using `Email` as the unique identifier
- Binary skill columns are stored as `1` (has skill) or `0` (no skill)
- Main Excel file is downloadable from the dashboard sidebar

## Scoring Formula

Final score is computed as:

`Final Score (%) = (Total Candidate Score / Max Score) * 100`

Weighted components:

- Identity Score
- Address Score
- Education Score
- Experience Score
- Skills Score

## Notes

- If a CV has no email, it is rejected to preserve unique candidate tracking.
- Batch upload endpoint: `/api/upload-cvs`.
- Direct filtered export download endpoint: `/api/export-download`.
