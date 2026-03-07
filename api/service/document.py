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
    async def analyze_resume(
        self, user_id: str, job_posting_id: str
    ) -> ResumeAnalyzeResponse:
        """
        Analyze resume details.
        """
        task = await call_resume_analysis.kiq(
            ResumeAnalyzeRequest(user_id=user_id, job_posting_id=job_posting_id)
        )
        task_result = await task.wait_result()
        
        if task_result.is_err:
            raise Exception(f"Worker Error: {task_result.error}")
        return task_result.return_value

    async def analyze_portfolio(
        self, user_id: str, job_posting_id: str
    ) -> PortfolioAnalyzeResponse:
        """
        Analyze portfolio details.
        """
        task = await call_portfolio_analysis.kiq(
            PortfolioAnalyzeRequest(user_id=user_id, job_posting_id=job_posting_id)
        )
        task_result = await task.wait_result()
        
        if task_result.is_err:
            raise Exception(f"Worker Error: {task_result.error}")
        return task_result.return_value
