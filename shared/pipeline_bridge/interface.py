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
from shared.schema.job_posting import JobPostingAnalyzeRequest, JobPostingAnalyzeResponse
from pipelines.applicant_evaluation.main import run_pipeline as run_applicant_evaluation
from pipelines.candidate_comparison.main import run_pipeline as run_candidate_comparison
from pipelines.job_analysis.main import run_pipeline as run_job_analysis
from pipelines.portfolio_analysis.main import run_pipeline as run_portfolio_analysis
from pipelines.resume_analysis.main import run_pipeline as run_resume_analysis


def call_job_analysis(request: JobPostingAnalyzeRequest) -> JobPostingAnalyzeResponse:
    return run_job_analysis(request)


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
