import asyncio
import os
import sys

# 프로젝트 루트 경로 추가 (모듈 import를 위해)
sys.path.append(os.getcwd())

from job_analysis.parser.extract.extractor import JobPostingExtractor


async def test_extraction():
    # 1. 샘플 데이터 로드
    # 프로젝트 루트 기준 경로
    root_dir = os.getcwd()
    sample_file = os.path.join(root_dir, "data", "job_posts", "saramin_1_result.txt")

    if not os.path.exists(sample_file):
        print(f"❌ Sample file not found: {sample_file}")
        return

    print(f"📂 Loading sample: {sample_file}")
    with open(sample_file, "r", encoding="utf-8") as f:
        text = f.read()

    print(f"📝 Text Length: {len(text)} chars")

    # 2. Extractor 초기화
    extractor = JobPostingExtractor()

    # 3. 추출 실행
    print("🚀 Starting Extraction with LLM...")
    try:
        result = await extractor.extract(text)

        if result:
            print("\n" + "=" * 50)
            print("✅ Extraction Result (Pydantic Model Print)")
            print("=" * 50)
            # 깔끔하게 필드별로 출력
            print(f"🏢 Company: {result.company_name}")
            print(f"📌 Title:   {result.job_title}")
            print(f"📅 Dates:   {result.start_date} ~ {result.end_date}")
            print("\n[🛠 Tech Stack]")
            for tech in result.tech_stacks:
                print(f" - {tech}")

            print("\n[📋 Requirements]")
            for req in result.requirements:
                print(f" - {req}")

            print("\n[🤖 AI Summary]")
            print(result.ai_summary)
            print("=" * 50)
        else:
            print("❌ Extraction returned None.")

    except Exception as e:
        print(f"❌ Error during extraction: {e}")


if __name__ == "__main__":
    asyncio.run(test_extraction())
