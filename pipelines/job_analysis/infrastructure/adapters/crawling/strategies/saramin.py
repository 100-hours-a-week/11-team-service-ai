from playwright.sync_api import Page
from ..base import BasePlaywrightCrawler
import logging

logger = logging.getLogger(__name__)


class SaraminCrawler(BasePlaywrightCrawler):
    """
    사람인(Saramin) 전용 크롤러.

    파싱 대상 DOM 경로:
        #content > .wrap_jview > section:first-of-type > .wrap_jv_cont
            ├── .wrap_jv_header                        → 공고 헤더
            ├── .jv_cont.jv_summary                    → 요약 정보
            ├── .jv_cont.jv_detail > .cont > iframe    → 공고 본문
            └── .jv_cont.jv_howto                      → 접수 방법
    """

    # 공통 루트: #content > .wrap_jview의 첫 번째 section 안의 .wrap_jv_cont
    _ROOT = "#content .wrap_jview > section:first-of-type .wrap_jv_cont"

    def _parse_page(self, page: Page) -> str:
        # 루트 컨테이너가 렌더링될 때까지 대기 (최초 진입점)
        try:
            page.wait_for_selector(self._ROOT, timeout=30000)
        except Exception:
            logger.warning(
                f"⚠️ Failed to load page content from {page.url} (Title: {page.title()})"
            )
            if "사람인" not in page.title() and "지원" not in page.title():
                logger.error(f"🚨 Suspicious Page Content (Bot Block?): {page.title()}")

        # 각 섹션을 순서대로 추출하여 리스트에 모음
        sections = [
            self._extract_header(page),
            self._extract_summary(page),
            self._extract_detail(page),
            self._extract_howto(page),
        ]

        # 빈 섹션 제거 후 합침
        return "\n\n".join(s for s in sections if s)

    # ── 섹션별 추출 메서드 ─────────────────────────────────

    def _extract_header(self, page: Page) -> str:
        """공고 헤더"""
        return self._extract_section(page, f"{self._ROOT} .wrap_jv_header")

    def _extract_summary(self, page: Page) -> str:
        """요약 정보"""
        return self._extract_section(page, f"{self._ROOT} .jv_cont.jv_summary")

    def _extract_howto(self, page: Page) -> str:
        """접수 방법"""
        return self._extract_section(page, f"{self._ROOT} .jv_cont.jv_howto")

    def _extract_detail(self, page: Page) -> str:
        """공고 본문 — .jv_cont.jv_detail > .cont 내 첫 번째 iframe 우선, fallback은 .cont 직접 추출"""
        cont_selector = f"{self._ROOT} .jv_cont.jv_detail .cont"

        if page.locator(cont_selector).count() == 0:
            logger.warning("⚠️ .jv_cont.jv_detail .cont not found")
            return ""

        # iframe이 있으면 그 안에서 추출
        iframe_locator = page.locator(f"{cont_selector} iframe").first
        if iframe_locator.count() > 0:
            return self._extract_iframe_content(iframe_locator)

        # iframe 없으면 .cont 본체를 직접 추출
        logger.info("No iframe in .jv_detail .cont, extracting directly.")
        return self._clean_html(page.locator(cont_selector).inner_html())

    # ── 공통 헬퍼 ──────────────────────────────────────────

    def _extract_section(self, page: Page, selector: str) -> str:
        """단일 셀렉터에서 텍스트를 추출하는 공통 헬퍼"""
        if page.locator(selector).count() > 0:
            text = self._clean_html(page.locator(selector).inner_html())
            logger.info(f"✅ Extracted: {selector}")
            return text

        logger.warning(f"⚠️ Section not found: {selector}")
        return ""

    def _extract_iframe_content(self, iframe_locator) -> str:
        """iframe 내부 콘텐츠를 추출 (.user_content 우선, fallback은 body)"""
        handle = iframe_locator.element_handle()
        if not handle:
            logger.warning("⚠️ Failed to get iframe element handle")
            return ""

        # iframe 내부 로드 완료 대기
        frame = handle.content_frame()
        if not frame:
            logger.warning("⚠️ iframe content_frame() returned None")
            return ""

        try:
            frame.wait_for_load_state("domcontentloaded", timeout=5000)
        except Exception:
            logger.warning("⚠️ iframe domcontentloaded timeout, proceeding anyway.")

        if frame.locator(".user_content").count() > 0:
            raw_html = frame.locator(".user_content").inner_html()
        else:
            raw_html = frame.locator("body").inner_html()

        logger.info("✅ Extracted iframe content")
        return self._clean_html(raw_html)
