from shared.schema.applicant import (
    CompareRequest,
    CompareResponse,
    EvaluateRequest,
    EvaluateResponse,
)
from shared.pipeline_bridge import call_applicant_evaluation, call_candidate_comparison


class ApplicantService:
    def evaluate_applicant(self, user_id: str, job_posting_id: str) -> EvaluateResponse:
        """
        Evaluate applicant resume against job posting.
        """
        return call_applicant_evaluation(
            EvaluateRequest(user_id=user_id, job_posting_id=job_posting_id)
        )

    def compare_applicants(
        self, user_id: str, job_posting_id: str, competitor: str
    ) -> CompareResponse:
        """
        Compare applicant with competitor.
        """
        return call_candidate_comparison(
            CompareRequest(
                user_id=user_id, job_posting_id=job_posting_id, competitor=competitor
            )
        )
