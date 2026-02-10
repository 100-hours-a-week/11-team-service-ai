from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict


class DocumentType(str, Enum):
    """
    지원 문서 유형 정의
    """
    RESUME = "RESUME"
    PORTFOLIO = "PORTFOLIO"


class ApplicantDocument(BaseModel):
    """
    지원자가 제출한 문서(이력서/포트폴리오) 도메인 모델
    원본 파일 정보와 추출된 텍스트 정보를 모두 포함
    """
    
    # 1. 문서 식별 및 메타데이터
    doc_type: DocumentType = Field(description="문서 유형 (RESUME, PORTFOLIO)")
    file_path: Optional[str] = Field(default=None, description="파일 저장 경로 (S3 등)")
    
    # 2. 파싱된 데이터 (분석용)
    extracted_text: Optional[str] = Field(default=None, description="추출된 텍스트 내용")
    
    model_config = ConfigDict(use_enum_values=True)  # Enum 값을 기본적으로 문자열 값으로 사용

    @property
    def is_analyzable(self) -> bool:
        """분석 가능한 상태인지(텍스트가 존재하고 유효한지) 확인"""
        return (
            self.extracted_text is not None 
            and len(self.extracted_text.strip()) > 50
        )
        
    def update_text(self, text: str):
        """텍스트 추출 결과 업데이트"""
        self.extracted_text = text