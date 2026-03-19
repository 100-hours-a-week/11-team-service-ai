# --- Exchange Name---
EXCHANGE_NAME = "scuad.ai.exchange"

# --- Queue Names (도메인별 큐 맵핑) ---
QUEUE_JOB_ANALYSIS = "scuad.ai.request.jobposting.queue"
QUEUE_RESUME_ANALYSIS = "scuad.ai.queue.resume"
QUEUE_PORTFOLIO_ANALYSIS = "scuad.ai.queue.portfolio"
QUEUE_APPLICANT_EVALUATION = "scuad.ai.queue.evaluation"
QUEUE_CANDIDATE_COMPARISON = "scuad.ai.queue.comparison"

# --- Task Names (워커 실행 함수 맵핑) ---
TASK_JOB_ANALYZE = "task.job.analyze"
TASK_JOB_DELETE = "task.job.delete"

TASK_RESUME_ANALYZE = "task.resume.analyze"
TASK_PORTFOLIO_ANALYZE = "task.portfolio.analyze"

TASK_APPLICANT_EVALUATE = "task.applicant.evaluate"
TASK_CANDIDATE_COMPARE = "task.candidate.compare"
