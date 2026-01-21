from shared.schema.applicant import EvaluateRequest, EvaluateResponse, CompetencyScore
from shared.schema.document import ResumeAnalyzeRequest, ResumeAnalyzeResponse

# Note: This pipeline serves both 'Applicant Evaluate' and 'Resume Analyze' APIs internally.
# For now, let's keep it generic or handle types.
# Given API structure, Applicant Evaluate uses EvaluateRequest.
# Document Resume Analyze uses ResumeAnalyzeRequest.
# Let's support union or make separate entry points if logic diverges.
# The user wants "each pipeline input as schema".
# Let's use EvaluateRequest as primary for "Evaluation".

def run_pipeline(request: EvaluateRequest) -> EvaluateResponse:
    """
    Execute the Applicant Evaluation Pipeline.
    Currently returns dummy data directly.
    """
    print(f"Running Applicant Evaluation Pipeline for user {request.user_id}, job {request.job_posting_id}")
    
    return EvaluateResponse(
        overall_score=85.5,
        competency_scores=[
            CompetencyScore(name="Skill Match (Pipeline)", score=90, description="Good match"),
            CompetencyScore(name="Experience", score=80, description="Decent"),
        ],
        one_line_review="Promising candidate (Pipeline Evaluated).",
        feedback_detail=f"Detailed feedback for user {request.user_id} based on pipeline analysis.",
    )

if __name__ == "__main__":
    # Test execution
    print(run_pipeline(EvaluateRequest(user_id="test_user", job_posting_id="12345")))
