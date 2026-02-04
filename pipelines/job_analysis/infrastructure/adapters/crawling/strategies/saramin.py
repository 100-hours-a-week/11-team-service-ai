from playwright.sync_api import Page
from ..base import BasePlaywrightCrawler
import logging

logger = logging.getLogger(__name__)


class SaraminCrawler(BasePlaywrightCrawler):
    """
    사람인(Saramin) 전용 크롤러.
    Iframe 내부에 공고 본문이 있는 경우를 탐색하여 텍스트를 병합합니다.
    """

    def _parse_page(self, page: Page) -> str:
        # 사람인은 로딩이 좀 걸릴 수 있음
        # networkidle은 광고 등으로 인해 너무 오래 걸리므로 제거하고 바로 selector 대기로 진입

        # 1. 헤더(.jv_header) 추출
        header_text = ""
        try:
            if page.locator(".jv_header").count() > 0:
                header_text = self._clean_html(page.locator(".jv_header").inner_html())
                logger.info("✅ Found header: .jv_header")
        except Exception:
            logger.warning("⚠️ Failed to extract header")

        # 2. 본문 컨테이너(.wrap_jv_cont) 대기 및 추출
        container_selector = ".wrap_jv_cont"
        iframe_selector = "#iframe_content_0"

        body_text = ""
        try:
            page.wait_for_selector(container_selector, timeout=5000)
            logger.info(f"✅ Found body container: {container_selector}")

            # 컨테이너 내부에 iframe이 있는지 확인
            iframe_element = page.locator(
                f"{container_selector} iframe{iframe_selector}"
            ).first

            if iframe_element.count() > 0:
                logger.info("found iframe, extracting content from iframe...")
                # Iframe 내부 콘텐츠 접근
                # element_handle() returns ElementHandle which has content_frame() method returning Frame
                handle = iframe_element.element_handle()
                frame = handle.content_frame() if handle else None
                if frame:
                    # Iframe 내부의 user_content (없으면 body 전체)
                    # user_content 클래스가 주로 본문임
                    if frame.locator(".user_content").count() > 0:
                        raw_html = frame.locator(".user_content").inner_html()
                    else:
                        raw_html = frame.content()

                    body_text = self._clean_html(raw_html)

            if not body_text:  # iframe이 없거나 실패했으면 직접 추출
                logger.info("Extracting content from container directly.")
                body_text = self._clean_html(
                    page.locator(container_selector).inner_html()
                )

        except Exception as e:
            logger.error(f"❌ Body selector not found or error: {e}")

        # 3. 채용 기간 및 접수 방법 추출 (.info_period)
        # .wrap_jv_cont 내부 혹은 전체에서 탐색하며, 첫 번째 요소만 가져옴
        period_text = ""
        try:
            # 우선순위: 컨테이너 내부 -> 전체
            period_selector = f"{container_selector} .info_period"
            
            target_element = None
            if page.locator(period_selector).count() > 0:
                target_element = page.locator(period_selector).first
                logger.info(f"✅ Found period info: {period_selector}")
            elif page.locator(".info_period").count() > 0:
                target_element = page.locator(".info_period").first
                logger.info("✅ Found period info: .info_period (Global)")
            
            if target_element:
                period_text = self._clean_html(target_element.inner_html())

        except Exception:
            logger.warning("⚠️ Failed to extract period info section")

        # 4. 헤더, 본문, 접수정보 합치기
        return f"{header_text}\n\n{body_text}\n\n{period_text}".strip()
