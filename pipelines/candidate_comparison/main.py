from shared.schema.applicant import CompareRequest, CompareResponse, ComparisonMetric


def run_pipeline(request: CompareRequest) -> CompareResponse:
    """
    Execute the Candidate Comparison Pipeline.
    Currently returns dummy data directly.
    """
    print(
        f"Running Candidate Comparison Pipeline for user {request.user_id} vs {request.competitor}"
    )

    return CompareResponse(
        comparison_metrics=[
            ComparisonMetric(name="Skill", my_score=80, competitor_score=70),
            ComparisonMetric(name="Experience", my_score=60, competitor_score=90),
        ],
        strengths_report="Pipeline says you are better at Skills.",
        weaknesses_report="Pipeline says competitor has more Experience.",
    )


if __name__ == "__main__":
    # Test execution
    print(
        run_pipeline(
            CompareRequest(user_id="user1", job_posting_id="12345", competitor="user2")
        )
    )
