from typing import Protocol


class WebCrawler(Protocol):
    """웹 크롤러 인터페이스"""

    def fetch(self, url: str) -> str:
        """URL의 콘텐츠를 가져옵니다. (Synchronous or Blocking I/O)"""
        ...
