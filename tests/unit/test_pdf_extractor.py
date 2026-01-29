import sys
import os
import io
import asyncio

# 현재 디렉토리(tests/unit)의 상위 상위 디렉토리(ai)를 path에 추가하여 모듈 import 가능하게 함
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from pipelines.applicant_evaluation.infrastructure.adapters.pdf_extractor import PyPdfExtractor

async def test_local_pdf_parsing():
    """
    로컬 폴더(download)에 있는 PDF 파일을 읽어서 텍스트를 추출하고
    결과를 parsed 폴더에 저장하는 단위 테스트 (Async)
    """
    print("\n🚀 Starting Local PDF Extraction Test (Async)...")

    # 1. Setup Logic
    extractor = PyPdfExtractor()

    # 2. Configure Paths
    # 프로젝트 루트: ai 폴더
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
    
    # 입력: tests/test_data/document/download (사용자 지정 소스)
    # (만약 테스트를 위해 임시로 origin 등 다른 폴더를 쓰고 싶다면 여기만 변경하면 됨)
    input_dir = os.path.join(project_root, "tests/test_data/document/download")
    
    # 출력: tests/test_data/document/parsed
    output_dir = os.path.join(project_root, "tests/test_data/document/parsed")
    
    # 출력 디렉토리 생성
    os.makedirs(output_dir, exist_ok=True)

    print(f"📂 Input Dir: {input_dir}")
    print(f"📂 Output Dir: {output_dir}")

    # 3. Check Input Files
    if not os.path.exists(input_dir):
        print(f"❌ Error: Input directory does not exist: {input_dir}")
        print("💡 Tip: 'tests/test_data/document/download' 폴더에 테스트할 PDF 파일을 넣어주세요.")
        return

    # PDF 파일 목록 조회
    pdf_files = [
        f for f in os.listdir(input_dir) 
        if os.path.isfile(os.path.join(input_dir, f)) 
        and f.lower().endswith('.pdf')
    ]
    
    if not pdf_files:
        print(f"⚠️ Warning: No PDF files found in {input_dir}")
        print("💡 Tip: 폴더에 PDF 파일이 있는지 확인해주세요.")
        return

    print(f"found {len(pdf_files)} PDF files.")

    # 4. Process Each File
    success_count = 0
    
    for filename in pdf_files:
        file_path = os.path.join(input_dir, filename)
        print(f"\n🔄 Processing: {filename}")

        try:
            # 파일 읽기 (바이너리 모드)
            with open(file_path, "rb") as f:
                pdf_content = f.read()

            # 텍스트 추출 실행 (Async call)
            extracted_text = await extractor.extract_text(pdf_content)

            # 결과 처리
            if not extracted_text:
                print(f"   ⚠️ No text extracted (Image-based or empty PDF?)")
                extracted_text = "(No text extracted)"
            else:
                print(f"   ✅ Extraction successful! ({len(extracted_text)} chars)")

            # 결과 저장 (.txt)
            result_filename = f"{os.path.splitext(filename)[0]}_parsed.txt"
            result_path = os.path.join(output_dir, result_filename)
            
            with open(result_path, "w", encoding="utf-8") as f:
                f.write(extracted_text)
            
            print(f"   💾 Saved to: {result_path}")
            success_count += 1

        except Exception as e:
            print(f"   ❌ Failed to extract text from {filename}: {e}")

    print(f"\n🎉 Test Completed. Successfully parsed {success_count}/{len(pdf_files)} files.")

if __name__ == "__main__":
    asyncio.run(test_local_pdf_parsing())
