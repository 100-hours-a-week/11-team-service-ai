
from shared.schema.document import (
    PortfolioAnalyzeRequest,
    PortfolioAnalyzeResponse,
    ResumeAnalyzeRequest,
    ResumeAnalyzeResponse,
)
from shared.pipeline_bridge import (
    call_portfolio_analysis,
    call_resume_analysis,
)


class DocumentService:
    def analyze_resume(self, user_id: str, job_posting_id: str) -> ResumeAnalyzeResponse:
        """
        Analyze resume details.
        """
        return call_resume_analysis(
            ResumeAnalyzeRequest(user_id=user_id, job_posting_id=job_posting_id)
        )

    def analyze_portfolio(
        self, user_id: str, job_posting_id: str
    ) -> PortfolioAnalyzeResponse:
        """
        Analyze portfolio details.
        """
        return call_portfolio_analysis(
            PortfolioAnalyzeRequest(user_id=user_id, job_posting_id=job_posting_id)
        )
