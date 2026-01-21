from shared.schema.job_posting import (
    JobPostingAnalyzeRequest,
    JobPostingAnalyzeResponse,
)
from shared.pipeline_bridge import call_job_analysis


class JobPostingService:
    def analyze_job_posting(self, url: str) -> JobPostingAnalyzeResponse:
        """
        Analyze job posting URL.
        Ideally calling the pipeline.
        """
        # Dummy Implementation
        return call_job_analysis(JobPostingAnalyzeRequest(url=url))

    def delete_job_posting(self, job_posting_id: str) -> dict:
        """
        Delete job posting data.
        """
        return {"deleted_id": job_posting_id}
