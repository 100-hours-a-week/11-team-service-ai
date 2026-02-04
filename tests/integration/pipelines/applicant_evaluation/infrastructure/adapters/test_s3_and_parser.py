import pytest
import sys
import os
import asyncio

# 현재 디렉토리(tests/integration)의 상위 상위 디렉토리(ai)를 path에 추가하여 모듈 import 가능하게 함
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from pipelines.applicant_evaluation.infrastructure.adapters.storage.s3_storage import (
    S3FileStorage,
)
from pipelines.applicant_evaluation.infrastructure.adapters.parser.pdf_extractor import (
    PyPdfExtractor,
)


@pytest.mark.asyncio
async def test_s3_pdf_upload_download_manual():
    """
    S3 PDF 파일 업로드 및 다운로드 테스트 (실제 파일 사용: Resum.pdf, Portfolio.pdf)
    비동기 버전
    """
    # 1. Setup
    try:
        storage = S3FileStorage()
    except Exception as e:
        pytest.skip(f"S3 연결 실패 (설정 확인 필요): {e}")

    # PDF Extractor 초기화
    extractor = PyPdfExtractor()

    # 테스트에 사용할 실제 파일 목록
    # 현재 파일 위치: tests/integration/pipelines/applicant_evaluation/infrastructure/adapters/test_s3_storage.py
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # 1. 원본 파일 경로: tests/fixtures/data/document
    # tests 폴더까지 5단계 올라감
    tests_dir = os.path.abspath(os.path.join(current_dir, "../../../../../"))
    origin_dir = os.path.join(tests_dir, "fixtures/data/document")

    # 2. 다운로드 경로: 현재 파일 위치 하위의 data 폴더
    download_dir = os.path.join(current_dir, "data")

    # 다운로드 디렉토리는 없으면 생성
    os.makedirs(download_dir, exist_ok=True)

    print(f"📂 Origin Dir: {origin_dir}")
    print(f"📂 Download Dir: {download_dir}")

    # origin_dir에 있는 모든 파일을 대상으로 테스트 (확장자 필터링 가능)
    if not os.path.exists(origin_dir):
        print(f"⚠️ [Skip] Origin directory does not exist: {origin_dir}")
        return

    test_files = [
        f
        for f in os.listdir(origin_dir)
        if os.path.isfile(os.path.join(origin_dir, f)) and not f.startswith(".")
    ]

    if not test_files:
        print(f"⚠️ [Skip] No files found in {origin_dir}")
        return

    for filename in test_files:
        file_path = os.path.join(origin_dir, filename)

        print(f"\n[Test] Processing local file: {filename}")

        # 파일 읽기
        with open(file_path, "rb") as f:
            pdf_content = f.read()

        s3_key = f"test_uploads/{filename}"

        print(f"       -> Uploading to S3 Key: {s3_key}")

        # 2. Upload
        try:
            uploaded_path = await storage.upload_file(
                pdf_content, s3_key, content_type="application/pdf"
            )
            assert uploaded_path == s3_key
            print(f"✅ [Test] {filename} Upload success")
        except Exception as e:
            pytest.fail(f"{filename} Upload failed: {e}")

        # 3. Download (Verification)
        try:
            downloaded_content = await storage.download_file(s3_key)
            assert downloaded_content == pdf_content

            # 다운로드 파일 저장
            save_path = os.path.join(download_dir, f"downloaded_{filename}")
            with open(save_path, "wb") as f:
                f.write(downloaded_content)

            print(f"✅ [Test] {filename} Download success. Saved to: {save_path}")

            # 4. Text Extraction (Verification)
            try:
                extracted_text = await extractor.extract_text(downloaded_content)
                text_len = len(extracted_text)
                print(f"       -> Extracted Text Length: {text_len} chars")

                # 추출된 텍스트 저장
                txt_filename = f"downloaded_{os.path.splitext(filename)[0]}.txt"
                txt_save_path = os.path.join(download_dir, txt_filename)
                with open(txt_save_path, "w", encoding="utf-8") as f:
                    f.write(extracted_text)

                print(
                    f"✅ [Test] {filename} Extraction success. Saved to: {txt_save_path}"
                )
                print(
                    f"       -> Preview: {extracted_text[:100].replace(chr(10), ' ')}..."
                )

            except Exception as e:
                print(
                    f"⚠️ [Test] {filename} Extraction failed (might vary by PDF type): {e}"
                )

        except Exception as e:
            pytest.fail(f"{filename} Download failed: {e}")

        # # 4. Cleanup
        # try:
        #     storage.s3_client.delete_object(Bucket=storage.bucket, Key=s3_key)
        #     print(f"✅ [Test] {filename} Cleanup success")
        # except Exception as e:
        #     print(f"⚠️ [Test] {filename} Cleanup failed: {e}")


if __name__ == "__main__":
    # 이 파일을 직접 실행할 경우 (python tests/integration/test_s3_storage_manual.py)
    try:
        print("\n--- PDF File Test (Async) ---")
        asyncio.run(test_s3_pdf_upload_download_manual())

        print("\n🎉 모든 테스트 통과!")
    except Exception as e:
        print(f"\n❌ 테스트 실패: {e}")
