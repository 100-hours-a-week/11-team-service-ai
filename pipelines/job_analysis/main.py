import logging
import asyncio

from shared.db.connection import get_db
from shared.schema.job_posting import (
    JobPostingAnalyzeRequest,
    JobPostingAnalyzeResponse,
    JobPostingDeleteResponse,
)
from job_analysis.service import JobAnalysisService
from job_analysis.simple_extraction_service import SimpleJobExtractionService


logger = logging.getLogger(__name__)

async def run_pipeline(request: JobPostingAnalyzeRequest) -> JobPostingAnalyzeResponse:
    """
    Job Analysis Pipeline Entrypoint (MSA)

    This function handles the entire lifecycle of a job analysis task:
    1. Manages DB session (Self-contained)
    2. Orchestrates crawling, extraction, and storage via Service
    3. Returns standardized response with transaction management
    """
    logger.info(f"🚀 [Pipeline Start] Job Analysis for URL: {request.url}")


    """
    단순 크롤링 및 추출 파이프라인 (DB 저장 없음)
    """
    service = SimpleJobExtractionService()
    return await service.extract_from_url(request.url)

    # try:
    #     # DB 세션 생성 (Context Manager로 자동 관리)
    #     async for session in get_db():
    #         # 트랜잭션 관리: Service 내부에서 commit 수행하거나 여기서 명시적 커밋
    #         # get_db()가 주는 session은 이미 autocommit=False
    #         service = JobAnalysisService(session)

    #         # 서비스 실행 (이제 Pydantic Model이 반환됨)
    #         response = await service.run_analysis(request.url)

    #         logger.info(f"✅ [Pipeline Success] Job ID: {response.job_posting_id}")
    #         return response
    # except Exception as e:
    #     logger.error(f"❌ [Pipeline Failed] Error: {e}", exc_info=True)
    #     raise

async def delete_pipeline(job_posting_id: int) -> JobPostingDeleteResponse:
    """
    Job Posting Deletion Pipeline Entrypoint
    """
    logger.info(f"🚀 [Pipeline Start] Delete Job Posting ID: {job_posting_id}")

    try:
        async for session in get_db():
            service = JobAnalysisService(session)
            # service.delete_job_posting returns int (deleted_id)
            deleted_id = await service.delete_job_posting(job_posting_id)
            
            if deleted_id is None: # None check added
                 raise ValueError(f"JobPosting {job_posting_id} not found or failed to delete.")

            logger.info(f"✅ [Pipeline Success] Deleted ID: {deleted_id}")
            return JobPostingDeleteResponse(deleted_id=deleted_id)
            
    except Exception as e:
        logger.error(f"❌ [Pipeline Failed] Delete Error: {e}", exc_info=True)
        raise
