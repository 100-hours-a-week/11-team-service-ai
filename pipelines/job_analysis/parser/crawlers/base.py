from abc import ABC, abstractmethod
import logging
import subprocess
from playwright.sync_api import sync_playwright, Page, Error as PlaywrightError
from bs4 import BeautifulSoup
from fastapi import HTTPException

# 로깅 설정
logger = logging.getLogger(__name__)

class BasePlaywrightCrawler(ABC):
    """
    모든 Playwright 기반 크롤러의 부모 클래스.
    공통적인 브라우저 실행 및 종료 로직을 담당합니다.
    """
    def __init__(self):
        self._ensure_browser_installed()
        self.user_agent = (
             "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
             "AppleWebKit/537.36 (KHTML, like Gecko) "
             "Chrome/120.0.0.0 Safari/537.36"
        )

    def _ensure_browser_installed(self):
        """브라우저 설치 확인 및 자동 설치"""
        try:
            subprocess.run(
                ["playwright", "--version"],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.info("🔧 Playwright not found or browsers missing. Installing chromium...")
            try:
                subprocess.run(["playwright", "install", "chromium"], check=True)
                logger.info("✅ Playwright chromium installed successfully.")
            except Exception as e:
                logger.error(f"❌ Failed to install Playwright browsers: {e}")
                raise RuntimeError("Could not install Playwright browsers.") from e

    def fetch(self, url: str) -> str:
        """
        공통 템플릿 메서드: 브라우저 실행 -> 페이지 이동 -> (자식 클래스 로직) -> 텍스트 반환
        """
        logger.info(f"🌐 [Playwright] Crawling URL: {url}")
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False)
                context = browser.new_context(
                    user_agent=self.user_agent,
                    viewport={"width": 1920, "height": 1080}
                )
                page = context.new_page()

                # 속도 최적화: 불필요한 리소스(이미지, 폰트 등) 로딩 차단
                def block_resources(route):
                    if route.request.resource_type in ["image", "media", "font", "stylesheet"]:
                        route.abort()
                    else:
                        route.continue_()

                # 모든 요청에 대해 인터셉터 등록
                page.route("**/*", block_resources)
                
                # 공통 페이지 이동 로직 (타임아웃은 넉넉히 주되, 불필요한 리소스를 막아둬서 빨리 끝남)
                page.goto(url, timeout=60000, wait_until="domcontentloaded")
                
                # 자식 클래스별 구체적인 파싱 로직 실행 (Hook)
                result_text = self._parse_page(page)
                
                browser.close()
                return result_text

        except PlaywrightError as e:
            logger.error(f"❌ Playwright error: {e}")
            raise HTTPException(status_code=400, detail=f"Crawling failed: {str(e)}")
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            raise HTTPException(status_code=500, detail=f"Internal crawler error: {str(e)}")

    @abstractmethod
    def _parse_page(self, page: Page) -> str:
        """
        각 사이트별 크롤러가 구체적으로 구현해야 하는 파싱 로직.
        Page 객체를 받아서 최종 텍스트를 반환해야 합니다.
        """
        pass

    def _clean_html(self, html_content: str) -> str:
        """HTML 정제 헬퍼 메서드 (BeautifulSoup 활용)"""
        soup = BeautifulSoup(html_content, "html.parser")
        
        unwanted_tags = ["script", "style", "noscript", "header", "footer", "nav", "aside", "form"]
        for tag in soup(unwanted_tags):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)
        import re
        text = re.sub(r"\n\s*\n", "\n\n", text)
        return text.strip()
