from shared.schema.job_posting import (
    JobPostingAnalyzeRequest,
    JobPostingAnalyzeResponse,
    JobPostingDeleteResponse,
)
from shared.pipeline_bridge import call_job_analysis, call_job_deletion


class JobPostingService:
    async def analyze_job_posting(self, url: str) -> JobPostingAnalyzeResponse:
        """
        Analyze job posting URL.
        Ideally calling the pipeline.
        """
        # Dummy Implementation
        return await call_job_analysis(JobPostingAnalyzeRequest(url=url))

    async def delete_job_posting(self, job_posting_id: int) -> JobPostingDeleteResponse:
        """
        Delete job posting data.
        """
        return await call_job_deletion(job_posting_id)
