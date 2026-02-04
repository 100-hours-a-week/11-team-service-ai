from playwright.sync_api import Page
from ..base import BasePlaywrightCrawler
import logging

logger = logging.getLogger(__name__)


class DefaultCrawler(BasePlaywrightCrawler):
    """
    특정 사이트 로직이 없는 경우 사용하는 기본 크롤러.
    Network Idle 상태까지 기다린 후 전체 HTML을 파싱합니다.
    """

    def _parse_page(self, page: Page) -> str:
        try:
            # 동적 로딩 대기 (최대 10초)
            page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            logger.warning(
                "⚠️ Network idle timeout in DefaultCrawler, proceeding anyway."
            )

        return self._clean_html(page.content())
