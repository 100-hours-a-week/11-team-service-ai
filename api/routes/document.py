from fastapi import APIRouter, status

from shared.schema.common_schema import ApiResponse
from shared.schema.document import (
    PortfolioAnalyzeRequest,
    PortfolioAnalyzeResponse,
    ResumeAnalyzeRequest,
    ResumeAnalyzeResponse,
)
from api.service.document import DocumentService

# Create separate routers or one? Spec has /api/v1/resume and /api/v1/portfolio.
# I'll create one router that handles both prefixes or just add endpoints.
# I will use Tags to separate them in swagger.

router = APIRouter(prefix="/ai/api/v1", tags=["Document Analysis"])


@router.post(
    "/resume/analyze",
    response_model=ApiResponse[ResumeAnalyzeResponse],
    status_code=status.HTTP_200_OK,
    summary="이력서 분석",
)
async def analyze_resume(request: ResumeAnalyzeRequest):
    service = DocumentService()
    result = await service.analyze_resume(request.user_id, request.job_posting_id)
    return ApiResponse(success=True, data=result)


@router.post(
    "/portfolio/analyze",
    response_model=ApiResponse[PortfolioAnalyzeResponse],
    status_code=status.HTTP_200_OK,
    summary="포트폴리오 분석",
)
async def analyze_portfolio(request: PortfolioAnalyzeRequest):
    service = DocumentService()
    result = await service.analyze_portfolio(request.user_id, request.job_posting_id)
    return ApiResponse(success=True, data=result)
