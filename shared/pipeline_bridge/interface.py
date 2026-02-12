from shared.schema.applicant import (
    CompareRequest,
    CompareResponse,
    EvaluateRequest,
    EvaluateResponse,
)
from shared.schema.document import (
    PortfolioAnalyzeRequest,
    PortfolioAnalyzeResponse,
    ResumeAnalyzeRequest,
    ResumeAnalyzeResponse,
)
from shared.schema.job_posting import (
    JobPostingAnalyzeRequest,
    JobPostingAnalyzeResponse,
    JobPostingDeleteResponse,
)
from applicant_evaluation.main import run_pipeline as run_applicant_evaluation
from candidate_comparison.main import run_pipeline as run_candidate_comparison
from job_analysis.main import (
    run_pipeline as run_job_analysis,
    delete_pipeline as delete_job_analysis,
)

# Resume Analysis와 Portfolio Analysis는 같은 파이프라인(resume_analysis)에서 처리
from resume_analysis.main import run_resume_analysis, run_portfolio_analysis


async def call_job_analysis(
    request: JobPostingAnalyzeRequest,
) -> JobPostingAnalyzeResponse:
    return await run_job_analysis(request)


async def call_job_deletion(job_posting_id: int) -> JobPostingDeleteResponse:
    return await delete_job_analysis(job_posting_id)


async def call_resume_analysis(request: ResumeAnalyzeRequest) -> ResumeAnalyzeResponse:
    return await run_resume_analysis(request)


async def call_applicant_evaluation(request: EvaluateRequest) -> EvaluateResponse:
    return await run_applicant_evaluation(request)


async def call_candidate_comparison(request: CompareRequest) -> CompareResponse:
    return await run_candidate_comparison(request)


async def call_portfolio_analysis(
    request: PortfolioAnalyzeRequest,
) -> PortfolioAnalyzeResponse:
    return await run_portfolio_analysis(request)
