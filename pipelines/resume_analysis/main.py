from shared.schema.document import ResumeAnalyzeRequest, ResumeAnalyzeResponse


async def run_pipeline(request: ResumeAnalyzeRequest) -> ResumeAnalyzeResponse:
    """
    Execute the Resume Analysis Pipeline.
    Currently returns dummy data directly.
    """
    print(f"Running Resume Analysis Pipeline for user {request.user_id}")

    return ResumeAnalyzeResponse(
        ai_analysis_report=f"Resume analysis for user {request.user_id} completed.",
        job_fit_score="High",
        experience_clarity_score="Clear",
        readability_score="Excellent",
    )


if __name__ == "__main__":
    # Test execution
    print(
        run_pipeline(ResumeAnalyzeRequest(user_id="test_user", job_posting_id="12345"))
    )
