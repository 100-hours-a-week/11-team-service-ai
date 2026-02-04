import logging

from shared.schema.job_posting import (
    JobPostingAnalyzeRequest,
    JobPostingAnalyzeResponse,
    JobPostingDeleteResponse,
)
from .application.services.extraction_service import JobExtractionService
from .infrastructure.adapters.crawling.router import DynamicRoutingCrawler
from .infrastructure.adapters.llm.job_extractor import OpenAiJobExtractor

from shared.config import settings
from .infrastructure.adapters.llm.mock_extractor import MockJobExtractor

logger = logging.getLogger(__name__)


# TODO: 공고분석 파이프라인 구현, 벡터db에만 공고 저장
async def run_pipeline(request: JobPostingAnalyzeRequest) -> JobPostingAnalyzeResponse:
    """
    크롤링 및 추출 파이프라인
    """
    # 설정에 따라 Extractor 주입 결정
    extractor_impl = MockJobExtractor() if settings.use_mock else OpenAiJobExtractor()

    service = JobExtractionService(
        crawler=DynamicRoutingCrawler(), extractor=extractor_impl
    )
    return await service.extract_job_data(request.url)


# TODO: 삭제 파이프라인 구현, 벡터db에 저장된 내용만 삭제
async def delete_pipeline(job_posting_id: int) -> JobPostingDeleteResponse:
    """
    Job Posting Deletion Pipeline Entrypoint
    """
    logger.info(f"🚀 [Pipeline Start] Delete Job Posting ID: {job_posting_id}")
    return JobPostingDeleteResponse(deleted_id=job_posting_id)
