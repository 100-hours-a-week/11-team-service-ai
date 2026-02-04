from ....domain.interface.crawler import WebCrawler
from .strategies.default import DefaultCrawler
from .strategies.saramin import SaraminCrawler
from .strategies.wanted import WantedCrawler


class DynamicRoutingCrawler(WebCrawler):
    """
    URL을 분석하여 적절한 실제 크롤러(Strategy)로 라우팅해주는 스마트 크롤러.
    Application Layer는 이 클래스 인스턴스 하나만 주입받으면 됨.
    """

    def fetch(self, url: str) -> str:
        # 정책 구현: URL 패턴에 따라 Strategy 선택
        strategy: WebCrawler
        if "saramin.co.kr" in url:
            strategy = SaraminCrawler()
        elif "wanted.co.kr" in url:
            strategy = WantedCrawler()
        else:
            strategy = DefaultCrawler()

        # 선택된 전략 실행 (위임)
        return strategy.fetch(url)
