from shared.schema.document import PortfolioAnalyzeRequest, PortfolioAnalyzeResponse

def run_pipeline(request: PortfolioAnalyzeRequest) -> PortfolioAnalyzeResponse:
    """
    Execute the Portfolio Analysis Pipeline.
    Currently returns dummy data directly.
    """
    print(f"Running Portfolio Analysis Pipeline for user {request.user_id}")
    
    return PortfolioAnalyzeResponse(
        ai_analysis_report="Portfolio shows strong skills (Pipeline Analysis).",
        problem_solving_score="Very Good",
        contribution_clarity_score="Clear",
        technical_depth_score="Deep",
    )

if __name__ == "__main__":
    # Test execution
    print(run_pipeline(PortfolioAnalyzeRequest(user_id="test_user", job_posting_id="12345")))
