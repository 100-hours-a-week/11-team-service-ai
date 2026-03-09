from shared.schema.applicant import (
    CompareRequest,
    EvaluateRequest,
)
from shared.schema.document import (
    PortfolioAnalyzeRequest,
    ResumeAnalyzeRequest,
)
from shared.schema.job_posting import (
    JobPostingAnalyzeRequest,
)


from shared.pipeline_bridge.broker import (
    broker_job,
    broker_resume,
    broker_portfolio,
    broker_evaluate,
    broker_compare,
)
from shared.pipeline_bridge.constants import (
    TASK_JOB_ANALYZE,
    TASK_JOB_DELETE,
    TASK_RESUME_ANALYZE,
    TASK_PORTFOLIO_ANALYZE,
    TASK_APPLICANT_EVALUATE,
    TASK_CANDIDATE_COMPARE,
)


@broker_job.task(task_name=TASK_JOB_ANALYZE)
async def call_job_analysis(request: JobPostingAnalyzeRequest):
    pass

@broker_job.task(task_name=TASK_JOB_DELETE)
async def call_job_deletion(job_posting_id: int):
    pass

@broker_evaluate.task(task_name=TASK_APPLICANT_EVALUATE)
async def call_applicant_evaluation(request: EvaluateRequest):
    pass

@broker_resume.task(task_name=TASK_RESUME_ANALYZE)
async def call_resume_analysis(request: ResumeAnalyzeRequest):
    pass

@broker_portfolio.task(task_name=TASK_PORTFOLIO_ANALYZE)
async def call_portfolio_analysis(request: PortfolioAnalyzeRequest):
    pass

@broker_compare.task(task_name=TASK_CANDIDATE_COMPARE)
async def call_candidate_comparison(request: CompareRequest):
    pass
