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
from job_analysis.main import run_pipeline as run_job_analysis, delete_pipeline as delete_job_analysis
from portfolio_analysis.main import run_pipeline as run_portfolio_analysis
from resume_analysis.main import run_pipeline as run_resume_analysis


def call_job_analysis(request: JobPostingAnalyzeRequest) -> JobPostingAnalyzeResponse:
    return run_job_analysis(request)


def call_job_deletion(job_posting_id: int) -> JobPostingDeleteResponse:
    return delete_job_analysis(job_posting_id)


def call_resume_analysis(request: ResumeAnalyzeRequest) -> ResumeAnalyzeResponse:
    return run_resume_analysis(request)


def call_applicant_evaluation(request: EvaluateRequest) -> EvaluateResponse:
    return run_applicant_evaluation(request)


def call_candidate_comparison(request: CompareRequest) -> CompareResponse:
    return run_candidate_comparison(request)


def call_portfolio_analysis(
    request: PortfolioAnalyzeRequest,
) -> PortfolioAnalyzeResponse:
    return run_portfolio_analysis(request)
