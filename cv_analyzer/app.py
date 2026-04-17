from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import os
from io import BytesIO
from werkzeug.utils import secure_filename
from cv_parser import CVParser
from scoring import ScoringSystem
from excel_manager import ExcelManager
from jobs_manager import JobsManager
import pandas as pd
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RUNTIME_BASE_DIR = BASE_DIR
UPLOAD_FOLDER = os.path.join(RUNTIME_BASE_DIR, 'uploads')
DATA_FOLDER = os.path.join(RUNTIME_BASE_DIR, 'data')
ALLOWED_EXTENSIONS = {'pdf', 'docx'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
APPLICANTS_FILE = os.path.join(DATA_FOLDER, 'applicants.xlsx')
JOBS_FILE = os.path.join(DATA_FOLDER, 'jobs.xlsx')

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Initialize components
cv_parser = CVParser()
scoring_system = ScoringSystem()
excel_manager = ExcelManager(os.path.join(DATA_FOLDER, 'applicants.xlsx'))
jobs_manager = JobsManager(os.path.join(DATA_FOLDER, 'jobs.xlsx'))

# Ensure folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DATA_FOLDER, exist_ok=True)

def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def process_uploaded_file(file_obj):
    """Process one uploaded CV and store parsed results in Excel."""
    if not file_obj or file_obj.filename == '':
        return {'success': False, 'status': 400, 'error': 'No file selected'}

    if not allowed_file(file_obj.filename):
        return {
            'success': False,
            'status': 400,
            'error': f"Invalid file type for {file_obj.filename}. Only PDF and DOCX are allowed."
        }

    filename = secure_filename(file_obj.filename)
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file_obj.save(file_path)

    should_delete_file = False
    try:
        candidate_data = cv_parser.parse_cv(file_path)
        if not candidate_data:
            should_delete_file = True
            return {'success': False, 'status': 400, 'error': f'Could not parse {filename}'}

        if not candidate_data.get('email'):
            should_delete_file = True
            return {
                'success': False,
                'status': 400,
                'error': f'Email not found in {filename}. Email is required to prevent duplicates.'
            }

        if excel_manager.candidate_exists(candidate_data['email']):
            should_delete_file = True
            return {
                'success': False,
                'status': 409,
                'duplicate': True,
                'error': f"Candidate with email {candidate_data['email']} already exists"
            }

        scores = scoring_system.get_score_breakdown(candidate_data)
        success = excel_manager.add_candidate(candidate_data, scores, filename)

        if not success:
            should_delete_file = True
            return {'success': False, 'status': 500, 'error': f'Failed to add candidate from {filename}'}

        return {
            'success': True,
            'status': 200,
            'candidate': {
                'id': candidate_data.get('email', ''),
                'name': f"{candidate_data.get('first_name', '')} {candidate_data.get('last_name', '')}".strip(),
                'email': candidate_data.get('email', ''),
                'score': scores.get('final_score', 0),
                'file_name': filename
            }
        }
    finally:
        if should_delete_file and os.path.exists(file_path):
            os.remove(file_path)

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/jobs', methods=['GET'])
def get_jobs():
    try:
        jobs = jobs_manager.get_all_jobs()
        return jsonify({'success': True, 'jobs': jobs, 'total': len(jobs)}), 200
    except Exception as e:
        print(f"Error in get_jobs: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/jobs', methods=['POST'])
def create_job():
    try:
        payload = request.get_json(silent=True) or {}

        required_fields = [
            'Job Title', 'Department / Category', 'Job Type', 'Work Mode', 'Location',
            'Job Description', 'Key Responsibilities', 'Requirements / Qualifications',
            'Experience Level', 'Application Deadline'
        ]
        missing_fields = [field for field in required_fields if not str(payload.get(field, '')).strip()]
        if missing_fields:
            return jsonify({
                'error': 'Missing required fields',
                'missing_fields': missing_fields
            }), 400

        result = jobs_manager.add_job(payload)
        if result.get('success'):
            return jsonify({
                'success': True,
                'message': 'Job posted successfully',
                'job': result.get('job', {})
            }), 201

        return jsonify({'error': result.get('error', 'Failed to create job')}), 500
    except Exception as e:
        print(f"Error in create_job: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/jobs/<job_id>', methods=['GET'])
def get_job(job_id):
    try:
        job = jobs_manager.get_job_by_id(job_id)
        if job:
            return jsonify({'success': True, 'job': job}), 200
        return jsonify({'error': 'Job not found'}), 404
    except Exception as e:
        print(f"Error in get_job: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload-cv', methods=['POST'])
def upload_cv():
    """Handle CV upload and parsing"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        result = process_uploaded_file(request.files['file'])

        if result.get('success'):
            return jsonify({
                'success': True,
                'message': 'CV uploaded and processed successfully',
                'candidate': result.get('candidate', {})
            }), 200

        payload = {'error': result.get('error', 'Unknown error')}
        if result.get('duplicate'):
            payload['duplicate'] = True
        return jsonify(payload), result.get('status', 500)
            
    except Exception as e:
        print(f"Error in upload_cv: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/upload-cvs', methods=['POST'])
def upload_cvs():
    """Handle batch CV uploads and return per-file outcomes."""
    try:
        files = request.files.getlist('files')
        if not files:
            return jsonify({'error': 'No files provided'}), 400

        results = []
        success_count = 0
        duplicate_count = 0
        failed_count = 0

        for file_obj in files:
            result = process_uploaded_file(file_obj)
            if result.get('success'):
                success_count += 1
                results.append({'status': 'uploaded', 'candidate': result.get('candidate', {})})
            elif result.get('duplicate'):
                duplicate_count += 1
                results.append({'status': 'duplicate', 'error': result.get('error', '')})
            else:
                failed_count += 1
                results.append({'status': 'failed', 'error': result.get('error', '')})

        return jsonify({
            'success': True,
            'summary': {
                'total_files': len(files),
                'uploaded': success_count,
                'duplicates': duplicate_count,
                'failed': failed_count
            },
            'results': results
        }), 200
    except Exception as e:
        print(f"Error in upload_cvs: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard', methods=['GET'])
def get_dashboard():
    """Get dashboard statistics"""
    try:
        stats = excel_manager.get_statistics()
        top_candidates = excel_manager.get_top_candidates(10)
        
        return jsonify({
            'success': True,
            'stats': stats,
            'top_candidates': top_candidates
        }), 200
    except Exception as e:
        print(f"Error in get_dashboard: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/candidates', methods=['GET'])
def get_candidates():
    """Get all candidates with optional filtering"""
    try:
        # Get query parameters
        filters = {}
        
        if request.args.get('min_score'):
            filters['min_score'] = float(request.args.get('min_score'))
        if request.args.get('max_score'):
            filters['max_score'] = float(request.args.get('max_score'))
        if request.args.get('gender'):
            filters['gender'] = request.args.get('gender')
        if request.args.get('country'):
            filters['country'] = request.args.get('country')
        if request.args.get('city'):
            filters['city'] = request.args.get('city')
        if request.args.get('skill'):
            filters['skill'] = request.args.get('skill')
        if request.args.get('education_level'):
            filters['education_level'] = request.args.get('education_level')
        if request.args.get('search'):
            filters['search'] = request.args.get('search')
        if request.args.get('min_experience'):
            filters['min_experience'] = int(request.args.get('min_experience'))
        
        candidates = excel_manager.filter_candidates(filters)
        
        return jsonify({
            'success': True,
            'candidates': candidates,
            'total': len(candidates)
        }), 200
    except Exception as e:
        print(f"Error in get_candidates: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/candidate/<email>', methods=['GET'])
def get_candidate_detail(email):
    """Get detailed information about a specific candidate"""
    try:
        candidate = excel_manager.get_candidate_by_email(email)
        
        if candidate:
            return jsonify({
                'success': True,
                'candidate': candidate
            }), 200
        else:
            return jsonify({'error': 'Candidate not found'}), 404
    except Exception as e:
        print(f"Error in get_candidate_detail: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/candidate/<email>', methods=['DELETE'])
def delete_candidate(email):
    """Delete a candidate"""
    try:
        success = excel_manager.delete_candidate(email)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Candidate deleted successfully'
            }), 200
        else:
            return jsonify({'error': 'Failed to delete candidate'}), 500
    except Exception as e:
        print(f"Error in delete_candidate: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/export', methods=['POST'])
def export_data():
    """Export filtered candidates to Excel"""
    try:
        data = request.json.get('data', [])
        
        if not data:
            return jsonify({'error': 'No data to export'}), 400
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'export_{timestamp}'
        
        success = excel_manager.export_to_excel(data, filename)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Data exported to {filename}.xlsx'
            }), 200
        else:
            return jsonify({'error': 'Failed to export data'}), 500
    except Exception as e:
        print(f"Error in export_data: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/export-download', methods=['POST'])
def export_and_download():
    """Export filtered candidates and stream the Excel file directly to browser."""
    try:
        payload = request.get_json(silent=True) or {}
        data = payload.get('data', [])

        if not data:
            return jsonify({'error': 'No data to export'}), 400

        df = pd.DataFrame(data)
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Filtered Applicants')
        output.seek(0)

        filename = f"filtered_candidates_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        return send_file(
            output,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        print(f"Error in export_and_download: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/download-excel', methods=['GET'])
def download_excel():
    """Download the main applicants Excel file"""
    try:
        excel_path = APPLICANTS_FILE
        
        if os.path.exists(excel_path):
            return send_file(excel_path, as_attachment=True, 
                           download_name='applicants.xlsx')
        else:
            return jsonify({'error': 'Excel file not found'}), 404
    except Exception as e:
        print(f"Error in download_excel: {e}")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({'error': 'File too large. Maximum size is 10MB'}), 413


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
