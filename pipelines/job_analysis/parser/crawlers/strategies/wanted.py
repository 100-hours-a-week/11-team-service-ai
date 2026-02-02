from playwright.sync_api import Page
from pipelines.job_analysis.parser.crawlers.base import BasePlaywrightCrawler
import logging

logger = logging.getLogger(__name__)


class WantedCrawler(BasePlaywrightCrawler):
    """
    원티드(Wanted) 전용 크롤러.
    SPA 로딩을 충분히 기다립니다.
    """

    def _parse_page(self, page: Page) -> str:
        # 원티드는 초기 로딩 후 API 호출로 데이터를 채우므로 대기가 필수
        try:
            # 더미 대기보다는 특정 요소 대기가 좋지만, 클래스명이 자주 바뀌므로 networkidle 사용
            page.wait_for_load_state("networkidle", timeout=20000)

            # (옵션) 스크롤을 끝까지 내려서 Lazy Loading 유도
            # page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            # page.wait_for_timeout(1000)
        except Exception:
            logger.warning("Wanted idle timeout")

        return self._clean_html(page.content())
