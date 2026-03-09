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


import logging
logger = logging.getLogger(__name__)

class DocumentService:
    async def analyze_resume(
        self, request: ResumeAnalyzeRequest
    ) -> ResumeAnalyzeResponse:
        """
        Analyze resume details.
        """
        task = await call_resume_analysis.kiq(request)
        task_result = await task.wait_result()
        
        if task_result.is_err:
            raise Exception(f"Worker Error: {task_result.error}")
        return task_result.return_value

    async def analyze_portfolio(
        self, request: PortfolioAnalyzeRequest
    ) -> PortfolioAnalyzeResponse:
        """
        Analyze portfolio details.
        """
        task = await call_portfolio_analysis.kiq(request)
        task_result = await task.wait_result()
        
        if task_result.is_err:
            raise Exception(f"Worker Error: {task_result.error}")
        return task_result.return_value
