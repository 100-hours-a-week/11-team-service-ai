from shared.schema.applicant import (
    CompareRequest,
    CompareResponse,
    EvaluateRequest,
    EvaluateResponse,
)
from shared.pipeline_bridge import call_applicant_evaluation, call_candidate_comparison


class ApplicantService:
    async def evaluate_applicant(
        self, user_id: str, job_posting_id: str
    ) -> EvaluateResponse:
        """
        Evaluate applicant resume against job posting.
        """
        # 1. 태스크를 큐에 비동기 전달 (Worker 스케줄링)
        task = await call_applicant_evaluation.kiq(
            EvaluateRequest(user_id=user_id, job_posting_id=job_posting_id)
        )
        
        # 2. Redis를 통해 워커의 처리 결과가 끝날 때까지 대기
        task_result = await task.wait_result()
        
        if task_result.is_err:
            raise Exception(f"Worker Error: {task_result.error}")
        return task_result.return_value

    async def compare_applicants(
        self, user_id: str, job_posting_id: str, competitor: str
    ) -> CompareResponse:
        """
        Compare applicant with competitor.
        """
        # 1. 태스크를 큐에 비동기 전달 (Worker 스케줄링)
        task = await call_candidate_comparison.kiq(
            CompareRequest(
                user_id=user_id, job_posting_id=job_posting_id, competitor=competitor
            )
        )
        
        # 2. Redis를 통해 워커의 처리 결과가 끝날 때까지 대기
        task_result = await task.wait_result()
        
        if task_result.is_err:
            raise Exception(f"Worker Error: {task_result.error}")
        return task_result.return_value
