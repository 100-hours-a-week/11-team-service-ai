import logging
import os
from pipelines.job_analysis.parser.crawlers.factory import CrawlerFactory

# 로그 설정
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("DevTester")


def test_crawlers():
    # 테스트할 URL 목록
    test_urls = [
        {
            "site": "Saramin_1",
            "url": "https://www.saramin.co.kr/zf_user/jobs/relay/view?isMypage=no&rec_idx=52837188&recommend_ids=eJxVj0EOhVAIA0%2Fz9w9Kga49iPe%2FxVcTRZeTKW2giQB6b7NfbfR2N2HX8gvLvZq3XRGWqCdcKfPXbSEXxpaWxVN12gNvS4LTfO1Wzy4UoamSEJ8wLb%2Fog8nzhQP%2F16sv6A%3D%3D&view_type=list&gz=1&t_ref_content=section_favor_001&t_ref=area_recruit&t_ref_area=410&relayNonce=fa32806a39847f628b9a&immediately_apply_layer_open=n#seq=0",
        },
        # 원티드 공고 예시 (필요시 유효한 URL로 교체 필요)
        {
            "site": "Saramin_2",
            "url": "https://www.saramin.co.kr/zf_user/jobs/relay/view?isMypage=no&rec_idx=52873755&recommend_ids=eJxdzrsNgEAMA9Bp6GPnXzPI7b8FEhIXoHxRZNuZZJavAo48nZVa5Grhj8vug3WH5%2FMuZgjdZEaDNVQEZIdlpBqminTElxxKq8cMCUfre2bIl7BXb5v1EJJyr7oARH8zsA%3D%3D&view_type=list&gz=1&t_ref_content=section_favor_001&t_ref=area_recruit&t_ref_area=309&relayNonce=505685c9ad7765076d6c&immediately_apply_layer_open=n#seq=0",
        },
        {
            "site": "Saramin_3",
            "url": "https://www.saramin.co.kr/zf_user/jobs/relay/view?isMypage=no&rec_idx=52857986&recommend_ids=eJxtzkEOAkEIRNHTuIcqCpq1B%2Bn738I40TBtXD4CP8giPFl7uT%2FqKSxaR%2B02%2FHDHNZCope%2B6t0iuuQbOmId8Ygma%2FvDTLqCmjcp23NrFNB70mGV2RA%2B7Gbr%2FJc%2BTePMF4F83fQ%3D%3D&view_type=list&gz=1&t_ref_content=section_favor_001&t_ref=area_recruit&t_ref_area=411&relayNonce=3caad83889b2bbe120b5&immediately_apply_layer_open=n#seq=0",
        },
    ]

    # 결과 저장 디렉토리
    output_dir = "./data/job_posts"
    os.makedirs(output_dir, exist_ok=True)

    print("\n" + "=" * 60)
    print("🚀 Starting Development Crawler Test")
    print("=" * 60 + "\n")

    for item in test_urls:
        site = item["site"]
        url = item["url"]

        print(f"🎯 Testing [{site}]")
        print(f"🔗 URL: {url}")

        try:
            # 1. 팩토리에서 크롤러 가져오기
            crawler = CrawlerFactory.get_crawler(url)
            print(f"🛠  Crawler Strategy: {crawler.__class__.__name__}")

            # 2. 크롤링 실행
            text = crawler.fetch(url)

            # 3. 결과 검증
            content_length = len(text)
            print(f"✅ Success! Content Length: {content_length} chars")

            if content_length < 50:
                print("⚠️  Warning: Content seems too short!")

            # 4. 파일 저장
            filename = f"{site.lower()}_result.txt"
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
