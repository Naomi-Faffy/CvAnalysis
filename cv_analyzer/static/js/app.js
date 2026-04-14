const state = {
    candidates: [],
    filteredCandidates: [],
    topCandidates: [],
    uploadResults: [],
    jobs: [],
    stats: {},
    charts: {}
};

const chartPalette = [
    '#22489A', '#32B24B', '#FF9F1C', '#3BA7D6', '#A56AE0', '#F06292', '#607D8B', '#26A69A'
];

document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    initUploadArea();
    initJobForm();
    bindFilterInputs();
    loadDashboard();
    loadCandidates();
    loadJobs();
});

function initNavigation() {
    const links = document.querySelectorAll('.nav-link');
    const tabs = document.querySelectorAll('.tab-content');

    links.forEach((link) => {
        link.addEventListener('click', (event) => {
            event.preventDefault();
            const tabName = link.getAttribute('data-tab');

            links.forEach((item) => item.classList.remove('active'));
            tabs.forEach((tab) => tab.classList.remove('active'));

            link.classList.add('active');
            document.getElementById(tabName).classList.add('active');
            document.getElementById('page-title').textContent = toTitleCase(tabName);
        });
    });
}

function initUploadArea() {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');

    dropZone.addEventListener('click', () => fileInput.click());

    fileInput.addEventListener('change', () => {
        if (fileInput.files.length) {
            uploadCVFiles(Array.from(fileInput.files));
            fileInput.value = '';
        }
    });

    ['dragenter', 'dragover'].forEach((eventName) => {
        dropZone.addEventListener(eventName, (event) => {
            event.preventDefault();
            dropZone.classList.add('drag-over');
        });
    });

    ['dragleave', 'drop'].forEach((eventName) => {
        dropZone.addEventListener(eventName, (event) => {
            event.preventDefault();
            dropZone.classList.remove('drag-over');
        });
    });

    dropZone.addEventListener('drop', (event) => {
        const files = Array.from(event.dataTransfer.files || []);
        if (files.length) {
            uploadCVFiles(files);
        }
    });
}

function bindFilterInputs() {
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('keydown', (event) => {
            if (event.key === 'Enter') {
                applyFilters();
            }
        });
    }
}

function initJobForm() {
    const form = document.getElementById('jobForm');
    if (!form) {
        return;
    }

    form.addEventListener('submit', async (event) => {
        event.preventDefault();

        const payload = {
            'Job Title': valueOf('jobTitle'),
            'Department / Category': valueOf('jobDepartment'),
            'Job Type': valueOf('jobType'),
            'Work Mode': valueOf('workMode'),
            'Location': valueOf('jobLocation'),
            'Job Description': valueOf('jobDescription'),
            'Key Responsibilities': valueOf('jobResponsibilities'),
            'Requirements / Qualifications': valueOf('jobRequirements'),
            'Experience Level': valueOf('experienceLevel'),
            'Application Deadline': valueOf('applicationDeadline')
        };

        try {
            const response = await fetch('/api/jobs', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });
            const result = await response.json();

            if (!response.ok || !result.success) {
                const message = result.missing_fields?.length
                    ? `Missing fields: ${result.missing_fields.join(', ')}`
                    : (result.error || 'Failed to post job.');
                showJobStatus(message, true);
                return;
            }

            showJobStatus('Job posted successfully.', false);
            resetJobForm(true);
            await loadJobs();
        } catch (error) {
            showJobStatus(`Job post failed: ${error.message}`, true);
        }
    });
}

async function loadJobs() {
    try {
        const response = await fetch('/api/jobs');
        const result = await response.json();
        if (!response.ok || !result.success) {
            return;
        }

        state.jobs = result.jobs || [];
        renderJobsBoard();
    } catch (error) {
        console.error('Failed to load jobs:', error);
    }
}

function renderJobsBoard() {
    const container = document.getElementById('jobsBoard');
    if (!container) {
        return;
    }

    if (!state.jobs.length) {
        container.innerHTML = '<div class="empty-state">No job posts yet. Use the form to publish the first role.</div>';
        return;
    }

    container.innerHTML = state.jobs.map((job) => {
        const title = job['Job Title'] || 'Untitled Role';
        const department = job['Department / Category'] || 'General';
        const jobType = job['Job Type'] || '';
        const workMode = job['Work Mode'] || '';
        const location = job['Location'] || '';
        const deadline = job['Application Deadline'] || '';
        const postDate = job['Post Date'] || '';
        const summary = truncateText(job['Job Description'] || '', 180);

        return `
            <div class="job-card" onclick="openJobModal('${encodeURIComponent(job['Job ID'] || '')}')">
                <div class="job-card-header">
                    <div>
                        <div class="job-card-title">${escapeHtml(title)}</div>
                        <div class="candidate-email">${escapeHtml(department)}</div>
                    </div>
                    <div class="job-pill">${escapeHtml(jobType)}</div>
                </div>
                <div class="job-meta">
                    <span class="job-pill">${escapeHtml(workMode)}</span>
                    <span class="job-pill">${escapeHtml(location)}</span>
                    <span class="job-pill">${escapeHtml(job['Experience Level'] || '')}</span>
                </div>
                <div class="job-summary">${escapeHtml(summary)}</div>
                <div class="candidate-email" style="margin-top: 10px;">
                    Post Date: ${escapeHtml(postDate || 'Auto detected')}
                    ${deadline ? ` | Deadline: ${escapeHtml(deadline)}` : ''}
                </div>
            </div>
        `;
    }).join('');
}

async function openJobModal(encodedJobId) {
    const jobId = decodeURIComponent(encodedJobId);
    try {
        const response = await fetch(`/api/jobs/${encodeURIComponent(jobId)}`);
        const result = await response.json();
        if (!response.ok || !result.success) {
            return;
        }

        const job = result.job;
        const details = document.getElementById('candidateDetail');
        details.innerHTML = `
            <h3>${escapeHtml(job['Job Title'] || '')}</h3>
            <div class="job-detail-grid">
                ${detailRow('Department / Category', job['Department / Category'])}
                ${detailRow('Job Type', job['Job Type'])}
                ${detailRow('Work Mode', job['Work Mode'])}
                ${detailRow('Location', job['Location'])}
                ${detailRow('Experience Level', job['Experience Level'])}
                ${detailRow('Application Deadline', job['Application Deadline'])}
                ${detailRow('Post Date', job['Post Date'])}
            </div>
            <div class="detail-section">
                <h4>Job Description</h4>
                <div class="detail-value" style="text-align:left; white-space:pre-wrap;">${escapeHtml(job['Job Description'] || '')}</div>
            </div>
            <div class="detail-section">
                <h4>Key Responsibilities</h4>
                <div class="detail-value" style="text-align:left; white-space:pre-wrap;">${escapeHtml(job['Key Responsibilities'] || '')}</div>
            </div>
            <div class="detail-section">
                <h4>Requirements / Qualifications</h4>
                <div class="detail-value" style="text-align:left; white-space:pre-wrap;">${escapeHtml(job['Requirements / Qualifications'] || '')}</div>
            </div>
        `;

        document.getElementById('candidateModal').classList.add('show');
    } catch (error) {
        console.error('Failed to open job details:', error);
    }
}

function showJobStatus(message, isError) {
    const statusEl = document.getElementById('jobFormStatus');
    if (!statusEl) {
        return;
    }
    statusEl.style.display = 'block';
    statusEl.className = `upload-status ${isError ? 'error' : 'success'}`;
    statusEl.textContent = message;
}

function resetJobForm(keepStatus = false) {
    const form = document.getElementById('jobForm');
    if (form) {
        form.reset();
    }
    if (!keepStatus) {
        const statusEl = document.getElementById('jobFormStatus');
        if (statusEl) {
            statusEl.style.display = 'none';
            statusEl.textContent = '';
        }
    }
}

async function uploadCVFiles(files) {
    const validFiles = (files || []).filter((file) => {
        const ext = String(file.name || '').split('.').pop().toLowerCase();
        return ['pdf', 'docx'].includes(ext);
    });

    if (!validFiles.length) {
        showUploadStatus('No valid files selected. Only PDF and DOCX are supported.', true);
        return;
    }

    showUploadStatus(`Uploading ${validFiles.length} CV file(s)...`, false);

    if (validFiles.length === 1) {
        await uploadSingleCV(validFiles[0]);
        return;
    }

    const formData = new FormData();
    validFiles.forEach((file) => formData.append('files', file));

    try {
        const response = await fetch('/api/upload-cvs', {
            method: 'POST',
            body: formData
        });
        const result = await response.json();

        if (!response.ok || !result.success) {
            showUploadStatus(result.error || 'Batch upload failed.', true);
            state.uploadResults = [
                {
                    file_name: 'Batch Request',
                    status: 'failed',
                    email: '',
                    score: '',
                    message: result.error || 'Batch upload failed.'
                }
            ];
            renderUploadResults();
            return;
        }

        state.uploadResults = (result.results || []).map((item) => {
            const candidate = item.candidate || {};
            return {
                file_name: candidate.file_name || '',
                status: item.status || 'failed',
                email: candidate.email || '',
                score: candidate.score !== undefined ? Number(candidate.score).toFixed(1) + '%' : '',
                message: item.error || ''
            };
        });
        renderUploadResults();

        (result.results || [])
            .filter((item) => item.status === 'uploaded' && item.candidate)
            .forEach((item) => appendRecentUpload(item.candidate));

        const summary = result.summary || {};
        showUploadStatus(
            `Batch complete: ${summary.uploaded || 0} uploaded, ${summary.duplicates || 0} duplicates, ${summary.failed || 0} failed.`,
            false
        );
        await Promise.all([loadDashboard(), loadCandidates()]);
    } catch (error) {
        showUploadStatus(`Batch upload failed: ${error.message}`, true);
    }
}

async function uploadSingleCV(file) {
    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/api/upload-cv', {
            method: 'POST',
            body: formData
        });
        const result = await response.json();

        if (!response.ok || !result.success) {
            showUploadStatus(result.error || 'Upload failed.', true);
            state.uploadResults = [
                {
                    file_name: file.name,
                    status: result.duplicate ? 'duplicate' : 'failed',
                    email: '',
                    score: '',
                    message: result.error || 'Upload failed.'
                }
            ];
            renderUploadResults();
            return;
        }

        showUploadStatus('CV uploaded successfully. Excel data has been updated.', false);
        appendRecentUpload(result.candidate);
        state.uploadResults = [
            {
                file_name: result.candidate.file_name || file.name,
                status: 'uploaded',
                email: result.candidate.email || '',
                score: result.candidate.score !== undefined ? Number(result.candidate.score).toFixed(1) + '%' : '',
                message: ''
            }
        ];
        renderUploadResults();
        await Promise.all([loadDashboard(), loadCandidates()]);
    } catch (error) {
        showUploadStatus(`Upload failed: ${error.message}`, true);
        state.uploadResults = [
            {
                file_name: file.name,
                status: 'failed',
                email: '',
                score: '',
                message: error.message
            }
        ];
        renderUploadResults();
    }
}

function renderUploadResults() {
    const card = document.getElementById('uploadResultsCard');
    const container = document.getElementById('uploadResultsTable');

    if (!card || !container) {
        return;
    }

    if (!state.uploadResults.length) {
        card.style.display = 'none';
        container.innerHTML = '';
        return;
    }

    card.style.display = 'block';

    const rows = state.uploadResults
        .map((item) => {
            const status = String(item.status || 'failed').toLowerCase();
            const statusClass = `status-${status}`;
            return `
                <tr>
                    <td>${escapeHtml(item.file_name || 'N/A')}</td>
                    <td><span class="status-badge ${statusClass}">${escapeHtml(status)}</span></td>
                    <td>${escapeHtml(item.email || '-')}</td>
                    <td>${escapeHtml(item.score || '-')}</td>
                    <td>${escapeHtml(item.message || '-')}</td>
                </tr>
            `;
        })
        .join('');

    container.innerHTML = `
        <table class="upload-results-table">
            <thead>
                <tr>
                    <th>File</th>
                    <th>Status</th>
                    <th>Email</th>
                    <th>Score</th>
                    <th>Message</th>
                </tr>
            </thead>
            <tbody>${rows}</tbody>
        </table>
    `;
}

function showUploadStatus(message, isError) {
    const statusEl = document.getElementById('uploadStatus');
    statusEl.style.display = 'block';
    statusEl.className = `upload-status ${isError ? 'error' : 'success'}`;
    statusEl.textContent = message;
}

function appendRecentUpload(candidate) {
    const wrapper = document.getElementById('uploadedCandidates');
    const list = document.getElementById('uploadedList');
    wrapper.style.display = 'block';

    const item = document.createElement('div');
    item.className = 'candidate-item';
    item.innerHTML = `
        <div class="candidate-info">
            <div class="candidate-name">${escapeHtml(candidate.name || 'Unknown')}</div>
            <div class="candidate-email">${escapeHtml(candidate.email || '')}</div>
        </div>
        <div class="candidate-score">${Number(candidate.score || 0).toFixed(1)}%</div>
    `;
    list.prepend(item);

    while (list.children.length > 6) {
        list.removeChild(list.lastElementChild);
    }
}

async function loadDashboard() {
    try {
        const response = await fetch('/api/dashboard');
        const result = await response.json();
        if (!response.ok || !result.success) {
            return;
        }

        state.stats = result.stats || {};
        state.topCandidates = result.top_candidates || [];

        renderStatsSummary();
        renderTopCandidates();
        renderCharts();
    } catch (error) {
        console.error('Failed to load dashboard:', error);
    }
}

async function loadCandidates(filters = {}) {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
        if (value !== null && value !== undefined && value !== '') {
            params.append(key, value);
        }
    });

    try {
        const response = await fetch(`/api/candidates?${params.toString()}`);
        const result = await response.json();
        if (!response.ok || !result.success) {
            return;
        }

        state.candidates = result.candidates || [];
        renderCandidatesTable('candidatesTable', state.candidates, true);

        if (Object.keys(filters).length > 0) {
            state.filteredCandidates = result.candidates || [];
            document.getElementById('filteredResults').style.display = 'block';
            renderCandidatesTable('filteredTable', state.filteredCandidates, false);
        }
    } catch (error) {
        console.error('Failed to load candidates:', error);
    }
}

function renderStatsSummary() {
    const total = state.stats.total_applicants || 0;
    const avg = Number(state.stats.average_score || 0);
    const topScore = state.topCandidates.length ? Number(state.topCandidates[0]['Final Score (%)'] || 0) : 0;

    document.getElementById('total-applicants').textContent = total;
    document.getElementById('avg-score').textContent = `${avg.toFixed(1)}%`;
    document.getElementById('top-score').textContent = `${topScore.toFixed(1)}%`;
}

function renderTopCandidates() {
    const container = document.getElementById('top-candidates');

    if (!state.topCandidates.length) {
        container.innerHTML = '<div class="empty-state">No candidates yet. Upload CVs to start ranking.</div>';
        return;
    }

    container.innerHTML = state.topCandidates
        .map((candidate, index) => {
            const first = candidate['First Name'] || '';
            const last = candidate['Last Name'] || '';
            const email = candidate['Email'] || '';
            const score = Number(candidate['Final Score (%)'] || 0);
            return `
                <div class="candidate-item" onclick="openCandidateModal('${encodeURIComponent(email)}')">
                    <div class="candidate-info">
                        <div class="candidate-name">#${index + 1} ${escapeHtml(`${first} ${last}`.trim())}</div>
                        <div class="candidate-email">${escapeHtml(email)}</div>
                    </div>
                    <div class="candidate-score">${score.toFixed(1)}%</div>
                </div>
            `;
        })
        .join('');
}

function renderCharts() {
    const stats = state.stats;

    createOrUpdateChart('scoreChart', 'bar', stats.score_distribution || {}, {
        label: 'Candidates',
        backgroundColor: '#22489A'
    });

    createOrUpdateChart('genderChart', 'pie', stats.gender_distribution || {}, {
        backgroundColor: chartPalette
    });

    const locationData = topN(stats.location_distribution || {}, 8);
    createOrUpdateChart('locationChart', 'bar', locationData, {
        label: 'Applicants',
        backgroundColor: '#32B24B'
    });

    const skillsData = topN(stats.skills_frequency || {}, 10);
    createOrUpdateChart('skillsChart', 'bar', skillsData, {
        label: 'Frequency',
        backgroundColor: '#FF9F1C'
    });

    createOrUpdateChart('educationChart', 'doughnut', stats.education_distribution || {}, {
        backgroundColor: chartPalette
    });

    createOrUpdateChart('experienceChart', 'line', stats.experience_distribution || {}, {
        label: 'Candidates',
        borderColor: '#22489A',
        backgroundColor: 'rgba(34,72,154,0.2)',
        fill: true,
        tension: 0.2
    });
}

function createOrUpdateChart(canvasId, type, dataObject, style = {}) {
    const labels = Object.keys(dataObject);
    const data = Object.values(dataObject);
    const element = document.getElementById(canvasId);

    if (!element) {
        return;
    }

    if (state.charts[canvasId]) {
        state.charts[canvasId].destroy();
    }

    if (!labels.length) {
        const ctx = element.getContext('2d');
        ctx.clearRect(0, 0, element.width, element.height);
        return;
    }

    state.charts[canvasId] = new Chart(element, {
        type,
        data: {
            labels,
            datasets: [
                {
                    label: style.label || 'Value',
                    data,
                    borderColor: style.borderColor || '#22489A',
                    backgroundColor: style.backgroundColor || chartPalette,
                    fill: style.fill || false,
                    tension: style.tension || 0
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: type === 'pie' || type === 'doughnut'
                }
            }
        }
    });
}

function renderCandidatesTable(containerId, candidates, includeActions) {
    const container = document.getElementById(containerId);

    if (!candidates.length) {
        container.innerHTML = '<div class="empty-state">No candidates found for this view.</div>';
        return;
    }

    const headers = [
        'Name', 'Email', 'Gender', 'Age', 'Location', 'Education', 'Experience', 'Skills', 'Final Score'
    ];

    const rows = candidates
        .map((candidate) => {
            const email = candidate['Email'] || '';
            const name = `${candidate['First Name'] || ''} ${candidate['Last Name'] || ''}`.trim();
            const score = Number(candidate['Final Score (%)'] || 0);
            const badge = scoreClass(score);

            return `
                <tr>
                    <td>${escapeHtml(name || 'N/A')}</td>
                    <td>${escapeHtml(email)}</td>
                    <td>${escapeHtml(candidate['Gender'] || 'Not specified')}</td>
                    <td>${escapeHtml(String(candidate['Age'] || ''))}</td>
                    <td>${escapeHtml(`${candidate['City'] || ''}, ${candidate['Country'] || ''}`.replace(/^,\s*/, ''))}</td>
                    <td>${escapeHtml(candidate['Education Level'] || 'Unknown')}</td>
                    <td>${escapeHtml(String(candidate['Years of Experience'] || 0))} yrs</td>
                    <td>${escapeHtml(candidate['Skills'] || '')}</td>
                    <td><span class="score ${badge}">${score.toFixed(1)}%</span></td>
                    ${includeActions ? `<td>
                        <button class="btn-secondary" onclick="openCandidateModal('${encodeURIComponent(email)}')">View</button>
                        <button class="btn-danger" onclick="deleteCandidate('${encodeURIComponent(email)}')">Delete</button>
                    </td>` : ''}
                </tr>
            `;
        })
        .join('');

    container.innerHTML = `
        <table>
            <thead>
                <tr>
                    ${headers.map((h) => `<th>${h}</th>`).join('')}
                    ${includeActions ? '<th>Actions</th>' : ''}
                </tr>
            </thead>
            <tbody>${rows}</tbody>
        </table>
    `;
}

async function openCandidateModal(encodedEmail) {
    const email = decodeURIComponent(encodedEmail);

    try {
        const response = await fetch(`/api/candidate/${encodeURIComponent(email)}`);
        const result = await response.json();

        if (!response.ok || !result.success) {
            return;
        }

        const candidate = result.candidate;
        const details = document.getElementById('candidateDetail');
        details.innerHTML = `
            <h3>${escapeHtml(`${candidate['First Name'] || ''} ${candidate['Last Name'] || ''}`.trim())}</h3>
            <div class="detail-section">
                <h4>Profile</h4>
                ${detailRow('Email', candidate['Email'])}
                ${detailRow('Phone', candidate['Phone'])}
                ${detailRow('Gender', candidate['Gender'])}
                ${detailRow('Age/DOB', candidate['Age/DOB'])}
                ${detailRow('City', candidate['City'])}
                ${detailRow('Country', candidate['Country'])}
            </div>
            <div class="detail-section">
                <h4>Education & Experience</h4>
                ${detailRow('Education', candidate['Education'])}
                ${detailRow('Education Level', candidate['Education Level'])}
                ${detailRow('Years of Experience', candidate['Years of Experience'])}
                ${detailRow('Current Role', candidate['Current Role'])}
            </div>
            <div class="detail-section">
                <h4>Scoring</h4>
                ${detailRow('Identity Score', candidate['Identity Score'])}
                ${detailRow('Address Score', candidate['Address Score'])}
                ${detailRow('Education Score', candidate['Education Score'])}
                ${detailRow('Experience Score', candidate['Experience Score'])}
                ${detailRow('Skills Score', candidate['Skills Score'])}
                ${detailRow('Final Score', `${Number(candidate['Final Score (%)'] || 0).toFixed(1)}%`)}
            </div>
            <div class="detail-section">
                <h4>Skills</h4>
                ${detailRow('Skills', candidate['Skills'])}
            </div>
        `;

        document.getElementById('candidateModal').classList.add('show');
    } catch (error) {
        console.error('Failed to open candidate details:', error);
    }
}

function closeCandidateModal() {
    document.getElementById('candidateModal').classList.remove('show');
}

window.addEventListener('click', (event) => {
    const modal = document.getElementById('candidateModal');
    if (event.target === modal) {
        closeCandidateModal();
    }
});

async function deleteCandidate(encodedEmail) {
    const email = decodeURIComponent(encodedEmail);
    if (!confirm(`Delete candidate ${email}?`)) {
        return;
    }

    try {
        const response = await fetch(`/api/candidate/${encodeURIComponent(email)}`, {
            method: 'DELETE'
        });
        const result = await response.json();
        if (!response.ok || !result.success) {
            alert(result.error || 'Delete failed.');
            return;
        }

        await Promise.all([loadDashboard(), loadCandidates()]);
    } catch (error) {
        console.error('Failed to delete candidate:', error);
    }
}

async function applyFilters() {
    const filters = {
        search: valueOf('searchInput'),
        min_score: valueOf('scoreRangeMin'),
        max_score: valueOf('scoreRangeMax'),
        gender: valueOf('genderFilter'),
        country: valueOf('countryFilter'),
        city: valueOf('cityFilter'),
        education_level: valueOf('educationFilter'),
        skill: valueOf('skillFilter'),
        min_experience: valueOf('minExperience')
    };

    await loadCandidates(filters);
}

function resetFilters() {
    [
        'searchInput',
        'scoreRangeMin',
        'scoreRangeMax',
        'genderFilter',
        'countryFilter',
        'cityFilter',
        'educationFilter',
        'skillFilter',
        'minExperience'
    ].forEach((id) => {
        const element = document.getElementById(id);
        if (element) {
            element.value = '';
        }
    });

    document.getElementById('filteredResults').style.display = 'none';
    loadCandidates();
}

async function exportFiltered() {
    const data = state.filteredCandidates.length ? state.filteredCandidates : state.candidates;

    if (!data.length) {
        alert('No records available to export.');
        return;
    }

    try {
        const response = await fetch('/api/export-download', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ data })
        });

        if (!response.ok) {
            let message = 'Export failed.';
            try {
                const result = await response.json();
                message = result.error || message;
            } catch (e) {
                message = 'Export failed.';
            }
            alert(message);
            return;
        }

        const blob = await response.blob();
        const downloadUrl = window.URL.createObjectURL(blob);
        const disposition = response.headers.get('Content-Disposition') || '';
        const filenameMatch = disposition.match(/filename="?([^";]+)"?/i);
        const filename = filenameMatch ? filenameMatch[1] : 'filtered_candidates.xlsx';

        const anchor = document.createElement('a');
        anchor.href = downloadUrl;
        anchor.download = filename;
        document.body.appendChild(anchor);
        anchor.click();
        anchor.remove();
        window.URL.revokeObjectURL(downloadUrl);
    } catch (error) {
        alert(`Export failed: ${error.message}`);
    }
}

function downloadExcel() {
    window.location.href = '/api/download-excel';
}

function detailRow(label, value) {
    return `
        <div class="detail-item">
            <span class="detail-label">${escapeHtml(String(label || ''))}</span>
            <span class="detail-value">${escapeHtml(String(value || 'N/A'))}</span>
        </div>
    `;
}

function scoreClass(score) {
    if (score >= 85) {
        return 'excellent';
    }
    if (score >= 70) {
        return 'good';
    }
    if (score >= 55) {
        return 'fair';
    }
    return 'poor';
}

function toTitleCase(value) {
    return String(value)
        .replace(/[-_]/g, ' ')
        .replace(/\w\S*/g, (txt) => txt.charAt(0).toUpperCase() + txt.substring(1).toLowerCase());
}

function topN(dataObject, limit) {
    return Object.fromEntries(
        Object.entries(dataObject)
            .sort((a, b) => b[1] - a[1])
            .slice(0, limit)
    );
}

function valueOf(id) {
    const element = document.getElementById(id);
    if (!element) {
        return '';
    }
    return String(element.value || '').trim();
}

function escapeHtml(value) {
    return String(value || '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

function truncateText(value, maxLength) {
    const text = String(value || '');
    if (text.length <= maxLength) {
        return text;
    }
    return `${text.slice(0, maxLength).trim()}...`;
}

window.applyFilters = applyFilters;
window.resetFilters = resetFilters;
window.exportFiltered = exportFiltered;
window.downloadExcel = downloadExcel;
window.openCandidateModal = openCandidateModal;
window.closeCandidateModal = closeCandidateModal;
window.deleteCandidate = deleteCandidate;
window.openJobModal = openJobModal;
window.resetJobForm = resetJobForm;
