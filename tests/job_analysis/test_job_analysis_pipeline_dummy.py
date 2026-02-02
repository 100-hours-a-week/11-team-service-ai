import asyncio
import logging

from shared.db.connection import get_db
from job_analysis.service import JobAnalysisService
from job_analysis.parser.extract.extractor import ExtractedJobData

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 더미 데이터 정의
DUMMY_EXTRACTED_DATA = ExtractedJobData(
    company_name="더미컴퍼니_0126",
    job_title="AI 엔지니어 (Python/LangChain)",
    tech_stacks=["python", "langchain"],
    main_tasks=["RAG 파이프라인 구축", "프롬프트 엔지니어링"],
    ai_summary="AI 엔지니어 채용 공고입니다. Python 및 LLM 활용 능력을 중시합니다.",
    qualification_requirements=["Python 3년 이상", "LLM 프로젝트 경험"],
    preferred_qualifications=["CS 전공자", "오픈소스 기여 경험"],
    start_date="2026-01-26",
    end_date="2026-02-28",
)


class MockJobAnalysisService(JobAnalysisService):
    """
    크롤링 및 추출 과정을 Skip하고 더미 데이터를 반환하는 Mock Service
    """

    async def _crawl_content(self, url: str) -> str:
        logger.info(f"🐛 [MOCK] Skipping Crawling for {url}")
        return "MOCK_HTML_CONTENT"

    async def _extract_data(self, raw_text: str):
        logger.info("🔍 [MOCK] Returning Dummy Extracted Data")
        # 실제로는 raw_text를 LLM에 보내서 추출하지만, 여기서는 더미 데이터 반환
        return DUMMY_EXTRACTED_DATA


async def main():
    logger.info("🚀 Starting Job Analysis Pipeline Test (Duplicate Logic + DB Save)...")

    # 테스트할 가짜 URL (매번 다르게 하거나 같게 하여 중복 테스트 가능)
    test_url = "https://www.naver.com/jobs/test1111"

    async for session in get_db():
        try:
            # Mock Service 초기화
            service = MockJobAnalysisService(session)

            # 파이프라인 실행
            response = await service.run_analysis(test_url)

            logger.info("✅ Pipeline Execution Complete!")
            logger.info(f"📄 Job ID: {response.job_posting_id}")
            logger.info(f"🏢 Company: {response.company_name}")
            logger.info(f"🛠️  Skills: {response.required_skills}")
            logger.info(f"♻️  Is Existing (Duplicate): {response.is_existing}")

        except Exception as e:
            logger.error(f"❌ Test Failed: {e}", exc_info=True)
            # 롤백은 main.py나 service레벨에서 처리되지만 여기서도 안전하게 로그

        break  # 1회 실행 후 종료


if __name__ == "__main__":
    asyncio.run(main())
