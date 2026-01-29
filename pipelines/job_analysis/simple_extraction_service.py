from typing import Any
import logging
import asyncio
from job_analysis.parser.crawlers.factory import CrawlerFactory
from job_analysis.parser.extract.extractor import JobPostingExtractor

logger = logging.getLogger(__name__)

class SimpleJobExtractionService:
    """
    단순 크롤링 및 데이터 추출만 수행하는 서비스
    DB 저장이나 중복 체크 없이 순수하게 데이터를 가져오는 역할
    """
    def __init__(self):
        self.extractor = JobPostingExtractor()

    async def extract_from_url(self, url: str) -> Any:
        """
        URL -> 크롤링 -> 추출 -> Dictionary(Pydantic Model) 반환
        """
        # 1. 크롤링 (Crawling)
        raw_text = await self._crawl_content(url)

        # 2. 추출 (Extraction)
        extracted_data = await self._extract_data(raw_text)

        # 3. Response 매핑 (DB 저장이 없으므로 ID는 임시값 0 사용)
        from shared.schema.job_posting import JobPostingAnalyzeResponse, RecruitmentPeriod

        recruitment_period = None
        if extracted_data.start_date or extracted_data.end_date:
            recruitment_period = RecruitmentPeriod(
                start_date=extracted_data.start_date,
                end_date=extracted_data.end_date
            )

        return JobPostingAnalyzeResponse(
            job_posting_id=0,  # 저장되지 않음
            is_existing=False,
            company_name=extracted_data.company_name,
            job_title=extracted_data.job_title,
            main_responsibilities=extracted_data.main_tasks if isinstance(extracted_data.main_tasks, list) else [],
            required_skills=extracted_data.tech_stacks if isinstance(extracted_data.tech_stacks, list) else [],
            recruitment_status="OPEN", # 기본값
            recruitment_period=recruitment_period,
            ai_summary=extracted_data.ai_summary or "",
            evaluation_criteria=[item.model_dump() for item in extracted_data.evaluation_criteria] if extracted_data.evaluation_criteria else []
        )

    async def _crawl_content(self, url: str) -> str:
        """URL에서 텍스트 콘텐츠를 크롤링합니다."""
        logger.info(f"🌐 Crawling URL: {url}")
        try:
            crawler = CrawlerFactory.get_crawler(url)
            # Playwright는 블로킹 I/O이므로 별도 스레드에서 실행
            raw_text = await asyncio.to_thread(crawler.fetch, url)

            if not raw_text or len(raw_text) < 50:
                raise ValueError("Crawled content is empty or too short.")

            logger.info(f"✅ Crawling successful. Length: {len(raw_text)} chars")
            return raw_text
        except ValueError as e:
            logger.error(f"❌ Crawling validation failed: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Crawling failed: {e}", exc_info=True)
            raise RuntimeError(f"Crawling failed: {e}") from e

    async def _extract_data(self, raw_text: str):
        """LLM을 사용하여 텍스트에서 구조화된 데이터를 추출합니다."""
        logger.info("🧠 Extracting data using LLM...")
        try:
            extracted_data = await self.extractor.extract(raw_text)
            if not extracted_data:
                raise RuntimeError("LLM Extraction returned empty result")
            logger.info("✅ Data extraction successful")
            return extracted_data
        except Exception as e:
            logger.error(f"❌ LLM extraction failed: {e}", exc_info=True)
            if "API" in str(e) or "OpenAI" in str(e):
                raise RuntimeError(f"OpenAI API error: {e}") from e
            raise RuntimeError(f"Data extraction failed: {e}") from e
