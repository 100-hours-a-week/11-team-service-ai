from playwright.sync_api import Page
from ..base import BasePlaywrightCrawler
import logging

logger = logging.getLogger(__name__)


class WantedCrawler(BasePlaywrightCrawler):
    """
    원티드(Wanted) 전용 크롤러.

    파싱 대상 DOM 경로:
        .JobContent_JobContent__Qb6DR                                   (루트)
            ├── .JobHeader_JobHeader__TZkW3                             → 공고 헤더
            └── .JobContent_descriptionWrapper__RMlfm                  (본문 래퍼)
                  ├── .JobDescription_JobDescription__s2Keo             → 공고 본문
                  ├── .JobDueTime_JobDueTime__yvhtg                    → 접수 기간
                  └── .JobWorkPlace_JobWorkPlace__xPlGe
                        └── ...map__24PDM
                              └── ...map__location__6pp2d              → 근무지
    """

    _ROOT = ".JobContent_JobContent__Qb6DR"
    _WRAPPER = f"{_ROOT} .JobContent_descriptionWrapper__RMlfm"

    def _parse_page(self, page: Page) -> str:
        # 원티드는 SPA — 루트 컨테이너가 렌더링될 때까지 대기
        try:
            page.wait_for_selector(self._ROOT, timeout=10000)
        except Exception:
            logger.warning(
                f"⚠️ Failed to load page content from {page.url} (Title: {page.title()})"
            )
            if "wanted" not in page.url:
                logger.error(f"🚨 Suspicious Page Content (Bot Block?): {page.title()}")

        sections = [
            self._extract_header(page),
            self._extract_description(page),
            self._extract_due_time(page),
            self._extract_workplace(page),
        ]

        return "\n\n".join(s for s in sections if s)

    # ── 섹션별 추출 메서드 ─────────────────────────────────

    def _extract_header(self, page: Page) -> str:
        """공고 헤더"""
        return self._extract_section(page, f"{self._ROOT} .JobHeader_JobHeader__TZkW3")

    def _extract_description(self, page: Page) -> str:
        """공고 본문 — "상세정보 더보기" 버튼이 있으면 클릭 후 전체 본문 추출"""
        description_selector = (
            f"{self._WRAPPER} .JobDescription_JobDescription__s2Keo"
        )
        wrapper_selector = (
            f"{description_selector}"
            " .JobDescription_JobDescription__paragraph__wrapper__WPrKC"
        )

        # wrapper 내부 버튼(더보기)이 있으면 클릭하여 전체 본문 확장
        button_locator = page.locator(f"{wrapper_selector} button")
        if button_locator.count() > 0:
            button_locator.first.click()
            # 클릭 후 버튼이 제거될 때까지 대기 (확장 완료 시점)
            try:
                button_locator.first.wait_for(state="hidden", timeout=3000)
            except Exception:
                logger.warning("⚠️ '더보기' 버튼 숨김 대기 타임아웃, 현재 상태로 진행.")
            logger.info("✅ Clicked '더보기' button in JobDescription")

        return self._extract_section(page, description_selector)

    def _extract_due_time(self, page: Page) -> str:
        """접수 기간"""
        return self._extract_section(
            page, f"{self._WRAPPER} .JobDueTime_JobDueTime__yvhtg"
        )

    def _extract_workplace(self, page: Page) -> str:
        """근무지"""
        return self._extract_section(
            page,
            f"{self._WRAPPER} .JobWorkPlace_JobWorkPlace__xPlGe"
            " .JobWorkPlace_JobWorkPlace__map__24PDM"
            " .JobWorkPlace_JobWorkPlace__map__location__6pp2d",
        )

    # ── 공통 헬퍼 ──────────────────────────────────────────

    def _extract_section(self, page: Page, selector: str) -> str:
        """단일 셀렉터에서 텍스트를 추출하는 공통 헬퍼"""
        if page.locator(selector).count() > 0:
            text = self._clean_html(page.locator(selector).inner_html())
            logger.info(f"✅ Extracted: {selector}")
            return text

        logger.warning(f"⚠️ Section not found: {selector}")
        return ""
