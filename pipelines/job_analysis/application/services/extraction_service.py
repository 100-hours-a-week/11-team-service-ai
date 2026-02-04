import logging
import asyncio
from shared.schema.job_posting import JobPostingAnalyzeResponse
from ...domain.interface.crawler import WebCrawler
from ...domain.interface.extractor import JobDataExtractor
from ..mapper import JobDataMapper

logger = logging.getLogger(__name__)


class JobExtractionService:
    """
    채용 공고 URL에서 데이터를 추출하는 응용 서비스
    (Infrastructure에 대한 의존성을 주입받거나 Factory를 통해 해결)
    """

    def __init__(self, crawler: WebCrawler, extractor: JobDataExtractor):
        # DIP: 구체 클래스 대신 인터페이스 사용
        # 외부에서(Main 등) 반드시 구현체를 주입해줘야 함
        self.crawler = crawler
        self.extractor = extractor

    async def extract_job_data(self, url: str) -> JobPostingAnalyzeResponse:
        """
        URL -> 크롤링 -> 추출 -> Response 반환 (DB 저장 없음)
        """
        # 0. 정책 검증 (Application Policy)
        # 현재는 사람인(Saramin) 공고만 지원함
        if "saramin.co.kr" not in url and "wanted.co.kr" not in url:
            raise ValueError("현재는 사람인(Saramin), 원티드(Wanted) 채용 공고만 지원합니다.")

        try:
            # 1. 크롤링 (Crawling)
            # Playwright는 Blocking I/O이므로 별도 스레드에서 실행
            logger.info(f"🌐 Crawling URL: {url}")
            raw_text = await asyncio.to_thread(self.crawler.fetch, url)

            if not raw_text or len(raw_text) < 50:
                raise ValueError("Crawled content is empty or too short.")

            # 2. 추출 (Extraction)
            extracted_data = await self.extractor.extract(raw_text)
            if not extracted_data:
                raise RuntimeError("LLM Extraction returned empty result")

            # 3. Response 매핑 (Domain Model -> Presentation Schema)
            return JobDataMapper.to_analyze_response(extracted_data)

        except Exception as e:
            logger.error(f"❌ Job extraction failed: {e}", exc_info=True)
            # Presentation Layer에서 처리하도록 예외 전파
            raise
