import logging
import asyncio

from shared.db.connection import get_db
from shared.schema.job_posting import (
    JobPostingAnalyzeRequest,
    JobPostingAnalyzeResponse,
)
from job_analysis.service import JobAnalysisService

logger = logging.getLogger(__name__)

async def run_pipeline(request: JobPostingAnalyzeRequest) -> JobPostingAnalyzeResponse:
    """
    Job Analysis Pipeline Entrypoint (MSA)
    
    This function handles the entire lifecycle of a job analysis task:
    1. Manages DB session (Self-contained)
    2. Orchestrates crawling, extraction, and storage via Service
    3. Returns standardized response
    """
    logger.info(f"🚀 [Pipeline Start] Job Analysis for URL: {request.url}")
    
    try:
        # DB 세션 생성 (Context Manager로 자동 관리)
        async for session in get_db():
            service = JobAnalysisService(session)
            
            # 서비스 실행 (이제 Pydantic Model이 반환됨)
            response = await service.run_analysis(request.url)
            
            logger.info(f"✅ [Pipeline Success] Job ID: {response.job_posting_id}")
            return response

    except Exception as e:
        logger.error(f"❌ [Pipeline Failed] Error: {e}", exc_info=True)
        # 에러 발생 시에도 적절한 Error Response를 반환하거나 raise
        raise e

# 테스트 실행용 (CLI)
if __name__ == "__main__":
    import asyncio
    
    async def main():
        req = JobPostingAnalyzeRequest(url="https://www.saramin.co.kr/zf_user/jobs/relay/view?rec_idx=49195689")
        res = await run_pipeline(req)
        print("Result:", res)

    asyncio.run(main())
