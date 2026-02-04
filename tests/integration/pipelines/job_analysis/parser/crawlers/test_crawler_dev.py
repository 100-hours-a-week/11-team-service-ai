import logging
import os
from pipelines.job_analysis.infrastructure.adapters.crawling.router import (
    DynamicRoutingCrawler,
)

# 로그 설정
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("DevTester")


def test_crawlers():
    # 테스트할 URL 목록
    test_urls = [
            "https://www.wanted.co.kr/wd/330563",
    ]

    # 결과 저장 디렉토리
    output_dir = "./tests/integration/pipelines/job_analysis/parser/data/"
    os.makedirs(output_dir, exist_ok=True)

    print("\n" + "=" * 60)
    print("🚀 Starting Development Crawler Test")
    print("=" * 60 + "\n")

    for url in test_urls:

        print(f"🎯 Testing [{url}]")

        try:
            # 1. 라우팅 크롤러 초기화
            crawler = DynamicRoutingCrawler()

            # (옵션) 내부 전략 확인을 위한 로깅은 router 내부 구현에 따름
            # 여기서는 fetch 호출만 하면 됨

            # 2. 크롤링 실행
            text = crawler.fetch(url)

            # 3. 결과 검증
            content_length = len(text)
            print(f"✅ Success! Content Length: {content_length} chars")

            if content_length < 50:
                print("⚠️  Warning: Content seems too short!")

            # 4. 파일 저장
            filename = f"crawlers_result.txt"
            filepath = os.path.join(output_dir, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(text)

            print(f"💾 Saved sample to: {filepath}")

            # 5. 본문 미리보기 (앞 200자)
            print("-" * 20 + " Preview " + "-" * 20)
            print(text[:200].replace("\n", " ") + "...")
            print("-" * 50)

        except Exception as e:
            print(f"❌ Failed: {e}")

        print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    test_crawlers()
