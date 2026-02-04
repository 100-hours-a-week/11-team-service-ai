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
        self.user_agent = (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )

    def fetch(self, url: str) -> str:
        """
        공통 템플릿 메서드: 브라우저 실행 -> 페이지 이동 -> (자식 클래스 로직) -> 텍스트 반환
        """
        # 봇 탐지 회피를 위해 무조건 Headful 모드 사용 (User Request)
        is_headless = False
        display = None

        try:
            # Linux 서버 등에서 가상 디스플레이(Xvfb) 시도
            from pyvirtualdisplay import Display

            display = Display(visible=False, size=(1920, 1080))
            display.start()
            logger.info("🖥️  Virtual Display(Xvfb) started.")
        except Exception as e:
            # Xvfb가 없으면(로컬 Mac 등) 실제 모니터 사용
            logger.warning(
                f"⚠️  Virtual Display not available (Error: {e}). Using physical display."
            )

        try:
            with sync_playwright() as p:
                try:
                    # 무조건 headless=False로 실행
                    browser = p.chromium.launch(
                        headless=is_headless,
                        args=[
                            "--disable-blink-features=AutomationControlled",
                            "--no-sandbox",
                            "--disable-setuid-sandbox",
                            "--disable-dev-shm-usage",  # 메모리 부족 충돌 방지 (Linux/Docker 필수)
                            "--disable-gpu",  # 가상 환경 렌더링 충돌 방지
                        ],
                    )
                except Exception as e:
                    # 브라우저 실행 실패 시 예외 처리
                    error_msg = str(e)
                    logger.error(f"❌ Browser Launch Failed: {error_msg}")

                    # 1. 브라우저 실행 파일이 없는 경우 (가장 근본적인 원인)
                    if "Executable doesn't exist" in error_msg:
                        logger.info("� Browser missing. Installing chromium...")
                        subprocess.run(
                            ["playwright", "install", "chromium"], check=True
                        )
                        logger.info("✅ Browser installed. Retrying launch...")
                        browser = p.chromium.launch(
                            headless=True,  # 설치 직후 안전하게 Headless로 시작
                            args=[
                                "--disable-blink-features=AutomationControlled",
                                "--no-sandbox",
                                "--disable-setuid-sandbox",
                                "--disable-dev-shm-usage",
                                "--disable-gpu",
                            ],
                        )

                    # 2. 시스템 의존성 라이브러리가 없는 경우 (Linux/Ubuntu 등)
                    elif "error while loading shared libraries" in error_msg:
                        logger.info(
                            "🔧 System dependencies missing. Running 'npx playwright install-deps'..."
                        )
                        try:
                            subprocess.run(
                                ["npx", "playwright", "install-deps", "chromium"],
                                check=True,
                            )
                            logger.info("✅ Dependencies installed. Retrying launch...")
                            # 의존성 설치 후 재시도 (Headless + Stealth)
                            browser = p.chromium.launch(
                                headless=True,
                                args=[
                                    "--disable-blink-features=AutomationControlled",
                                    "--no-sandbox",
                                    "--disable-setuid-sandbox",
                                    "--disable-dev-shm-usage",
                                    "--disable-gpu",
                                ],
                            )
                        except Exception as dep_err:
                            logger.error(
                                f"❌ Failed to install dependencies: {dep_err}"
                            )
                            raise e

                    # 3. Xvfb(XServer)가 없어서 Headful 모드가 실패한 경우 (환경 설정 문제)
                    elif (
                        "No XServer running" in error_msg
                        or "headless: true" in error_msg
                    ):
                        logger.warning(
                            "🚨 Xvfb not found! Falling back to 'headless=True' with Stealth options to prevent crash."
                        )
                        browser = p.chromium.launch(
                            headless=True,  # 자동 폴백
                            args=[
                                "--disable-blink-features=AutomationControlled",
                                "--no-sandbox",
                                "--disable-setuid-sandbox",
                                "--disable-dev-shm-usage",
                                "--disable-gpu",
                            ],
                        )

                    else:
                        # 그 외 알 수 없는 에러는 그대로 발생
                        raise e

                context = browser.new_context(
                    user_agent=self.user_agent,
                    viewport={"width": 1920, "height": 1080},
                    locale="ko-KR",
                    ignore_https_errors=True,  # HTTPS 에러 무시
                )

                # navigator.webdriver 값 제거 (가장 중요한 탐지 방지 스크립트)
                context.add_init_script(
                    "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
                )

                # 실제 사용자처럼 보이게 하기 위한 추가 스크립트 주입 (Stealth)
                context.add_init_script("""
                    // 1. Plugins/MimeTypes 모킹 (Headless는 보통 비어있음)
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5] 
                    });
                    
                    // 2. window.chrome 속성 유지
                    window.chrome = { runtime: {} };

                    // 3. 권한 요청 자동 통과 (Notification 등)
                    const originalQuery = window.navigator.permissions.query;
                    window.navigator.permissions.query = (parameters) => (
                        parameters.name === 'notifications' ?
                        Promise.resolve({ state: 'granted' }) :
                        originalQuery(parameters)
                    );

                    // 4. WebGL 벤더 정보 조작
                    const getParameter = WebGLRenderingContext.prototype.getParameter;
                    WebGLRenderingContext.prototype.getParameter = function(parameter) {
                        if (parameter === 37445) return 'Intel Inc.';
                        if (parameter === 37446) return 'Intel Iris OpenGL Engine';
                        return getParameter(parameter);
                    };
                """)

                page = context.new_page()

                # 속도 최적화: 불필요한 리소스(이미지, 폰트 등) 로딩 차단
                def block_resources(route):
                    if route.request.resource_type in [
                        "image",
                        "media",
                        "font",
                        "stylesheet",
                        "other",  # 광고 스크립트 등 기타 리소스
                    ]:
                        route.abort()
                    else:
                        route.continue_()

                # 모든 요청에 대해 인터셉터 등록
                page.route("**/*", block_resources)

                # 공통 페이지 이동 로직 (Timeout 방지 및 속도 개선)
                # 1. commit(응답 헤더 수신)까지만 기다림
                try:
                    # 타임아웃 15초로 단축 (Fail Fast)
                    page.goto(url, timeout=15000, wait_until="commit")
                except PlaywrightError as e:
                    logger.warning(f"⚠️ Initial navigation warning: {e}")

                # 2. DOM 로드 대기 (최대 10초)
                try:
                    page.wait_for_load_state("domcontentloaded", timeout=10000)
                except Exception:
                    logger.warning(
                        "⚠️ DOM load timeout. Proceeding with partial content."
                    )

                # 3. 최소한의 콘텐츠(body)가 렌더링될 때까지 짧게 대기 (1초)
                try:
                    page.wait_for_selector("body", timeout=1000)
                except Exception:
                    pass

                # 자식 클래스별 구체적인 파싱 로직 실행 (Hook)
                result_text = self._parse_page(page)

                browser.close()
                return result_text

        except PlaywrightError as e:
            logger.error(f"❌ Playwright error: {e}")
            raise HTTPException(status_code=400, detail=f"Crawling failed: {str(e)}")
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            raise HTTPException(
                status_code=500, detail=f"Internal crawler error: {str(e)}"
            )
        finally:
            if display:
                display.stop()

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

        unwanted_tags = [
            "script",
            "style",
            "noscript",
            "header",
            "footer",
            "nav",
            "aside",
            "form",
        ]
        for tag in soup(unwanted_tags):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)
        import re

        text = re.sub(r"\n\s*\n", "\n\n", text)
        return text.strip()
