from fastapi import APIRouter, status

from shared.schema.applicant import (
    CompareRequest,
    CompareResponse,
    EvaluateRequest,
    EvaluateResponse,
)
from shared.schema.common_schema import ApiResponse
from api.service.applicant import ApplicantService

router = APIRouter(prefix="/api/v1/applicant", tags=["Applicant"])


@router.post(
    "/evaluate",
    response_model=ApiResponse[EvaluateResponse],
    status_code=status.HTTP_200_OK,
    summary="지원자 평가",
)
async def evaluate_applicant(request: EvaluateRequest):
    service = ApplicantService()
    result = await service.evaluate_applicant(request.user_id, request.job_posting_id)
    return ApiResponse(success=True, data=result)


@router.post(
    "/compare",
    response_model=ApiResponse[CompareResponse],
    status_code=status.HTTP_200_OK,
    summary="지원자 비교",
)
async def compare_applicants(request: CompareRequest):
    service = ApplicantService()
    result = await service.compare_applicants(
        request.user_id, request.job_posting_id, request.competitor
    )
    return ApiResponse(success=True, data=result)
