import io
import asyncio
import pdfplumber
from ....domain.interface.adapter_interfaces import TextExtractor


class PyPdfExtractor(TextExtractor):
    """
    pdfplumber 라이브러리를 사용한 PDF 텍스트 추출기 구현체 (Async Wrapper)
    """

    async def extract_text(self, pdf_content: bytes) -> str:
        """
        메모리 상의 PDF 바이너리에서 텍스트를 추출 (비동기)
        CPU 바운드 작업이므로 별도 스레드에서 실행
        """

        def _extract_sync():
            try:
                # BytesIO를 사용하여 메모리 스트림 생성
                pdf_stream = io.BytesIO(pdf_content)

                full_text = []
                with pdfplumber.open(pdf_stream) as pdf:
                    for page in pdf.pages:
                        text = page.extract_text()
                        if text:
                            full_text.append(text)

                # 페이지 내용을 줄바꿈으로 연결
                return "\n\n".join(full_text).strip()

            except Exception as e:
                # 로그를 남기는 것이 좋지만, 여기서는 간단히 빈 문자열 반환하거나 에러 출력
                print(f"PDF extraction failed with pdfplumber: {e}")
                return ""

        return await asyncio.to_thread(_extract_sync)
