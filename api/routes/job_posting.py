from fastapi import APIRouter, status

from shared.schema.common_schema import ApiResponse
from shared.schema.job_posting import (
    JobPostingAnalyzeRequest,
    JobPostingAnalyzeResponse,
    JobPostingDeleteResponse,
)
from api.service.job_posting import JobPostingService

router = APIRouter(prefix="/api/v1/job-posting", tags=["Job Posting"])


@router.post(
    "/analyze",
    response_model=ApiResponse[JobPostingAnalyzeResponse],
    status_code=status.HTTP_200_OK,
    summary="채용 공고 분석",
)
async def analyze_job_posting(request: JobPostingAnalyzeRequest):
    service = JobPostingService()
    result = await service.analyze_job_posting(request.url)
    return ApiResponse(success=True, data=result)


@router.delete(
    "/{job_posting_id}",
    response_model=ApiResponse[JobPostingDeleteResponse],
    status_code=status.HTTP_200_OK,
    summary="공고 삭제",
)
async def delete_job_posting(job_posting_id: int):
    service = JobPostingService()
    result = await service.delete_job_posting(job_posting_id)
    return ApiResponse(success=True, data=result)
