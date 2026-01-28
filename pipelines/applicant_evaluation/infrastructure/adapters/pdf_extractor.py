import io
import pypdf
from typing import Optional
from ...domain.interface.adapter_interfaces import TextExtractor

class PyPdfExtractor(TextExtractor):
    """
    PyPDF2 (pypdf) 라이브러리를 사용한 PDF 텍스트 추출기 구현체
    """
    def extract_text(self, pdf_content: bytes) -> str:
        """
        메모리 상의 PDF 바이너리에서 텍스트를 추출
        """
        try:
            # BytesIO를 사용하여 메모리 스트림 생성
            pdf_stream = io.BytesIO(pdf_content)
            reader = pypdf.PdfReader(pdf_stream)
            
            extracted_text = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    extracted_text.append(text)
            
            full_text = "\n".join(extracted_text)
            
            # 간단한 후처리 (불필요한 공백 제거 등)
            return full_text.strip()
            
        except Exception as e:
            # 로그를 남기는 것이 좋지만, 여기서는 간단히 빈 문자열 반환하거나 에러 전파
            print(f"PDF extraction failed: {e}")
            return ""
