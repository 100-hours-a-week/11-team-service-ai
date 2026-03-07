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
        task = await call_job_analysis.kiq(JobPostingAnalyzeRequest(url=url))
        task_result = await task.wait_result()
        
        if task_result.is_err:
            raise Exception(f"Worker Error: {task_result.error}")
        return task_result.return_value

    async def delete_job_posting(self, job_posting_id: int) -> JobPostingDeleteResponse:
        """
        Delete job posting data.
        """
        task = await call_job_deletion.kiq(job_posting_id)
        task_result = await task.wait_result()
        
        if task_result.is_err:
            raise Exception(f"Worker Error: {task_result.error}")
        return task_result.return_value
