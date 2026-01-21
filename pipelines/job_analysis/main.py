from shared.schema.job_posting import JobPostingAnalyzeRequest, JobPostingAnalyzeResponse

def run_pipeline(request: JobPostingAnalyzeRequest) -> JobPostingAnalyzeResponse:
    """
    Execute the Job Analysis Pipeline.
    Currently returns dummy data directly.
    """
    print(f"Running Job Analysis Pipeline for url: {request.url}")
    
    return JobPostingAnalyzeResponse(
        job_posting_id=12345,
        is_existing=False,
        company_name="Analyzed Company (Pipeline)",
        job_title="Analyzed Job Title",
        main_responsibilities=["Resp 1", "Resp 2"],
        required_skills=["Skill A", "Skill B"],
        recruitment_status="Open",
        recruitment_period=None,
        ai_summary=f"Analysis of {request.url} completed by Job Analysis Pipeline.",
    )

if __name__ == "__main__":
    # Test execution
    print(run_pipeline(JobPostingAnalyzeRequest(url="http://test.url")))
