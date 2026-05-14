from cv_analyzer.scoring import ScoringSystem
from cv_analyzer.excel_manager import ExcelManager
from cv_analyzer.jobs_manager import JobsManager

try:
    m = ExcelManager(r'c:\Users\TafaraChitiyo-I-\Documents\CV Analysis\cv_analyzer\data\applicants.xlsx')
    j = JobsManager(r'c:\Users\TafaraChitiyo-I-\Documents\CV Analysis\cv_analyzer\data\jobs.xlsx')
    s = ScoringSystem()
    updated = m.refresh_candidate_scores(s, j)
    print(f'successfully updated {updated} candidate rows')
except Exception as e:
    print(f'error: {e}')
    import traceback
    traceback.print_exc()
