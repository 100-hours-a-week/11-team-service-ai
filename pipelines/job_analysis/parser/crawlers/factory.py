from pipelines.job_analysis.parser.crawlers.base import BasePlaywrightCrawler
from pipelines.job_analysis.parser.crawlers.strategies.default import DefaultCrawler
from pipelines.job_analysis.parser.crawlers.strategies.saramin import SaraminCrawler
from pipelines.job_analysis.parser.crawlers.strategies.wanted import WantedCrawler


class CrawlerFactory:
    """
    URL을 분석하여 적합한 Crawler 인스턴스를 반환하는 팩토리 클래스.
    """

    @staticmethod
    def get_crawler(url: str) -> BasePlaywrightCrawler:
        if "saramin.co.kr" in url:
            return SaraminCrawler()
        elif "wanted.co.kr" in url:
            return WantedCrawler()
        else:
            return DefaultCrawler()
