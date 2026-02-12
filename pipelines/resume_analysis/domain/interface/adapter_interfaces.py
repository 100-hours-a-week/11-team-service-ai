from typing import Protocol
from ..models.job import JobInfo
from ..models.report import AnalysisReport
from ..models.document import DocumentType


class FileStorage(Protocol):
    """파일 스토리지 (S3 등) 인터페이스 (Async)"""

    async def download_file(self, file_path: str) -> bytes:
        """파일 경로로 바이너리 데이터 다운로드"""
        ...


class TextExtractor(Protocol):
    """문서 파서 (PDF -> Text) 인터페이스 (Async)"""

    async def extract_text(self, pdf_content: bytes) -> str:
        """PDF 바이너리 파일 콘텐츠에서 텍스트 추출"""
        ...


class AnalystAgent(Protocol):
    """
    AI 분석 에이전트 인터페이스 (Async)
    """

    async def run_analysis(
        self,
        job_info: JobInfo,
        document_text: str,
        doc_type: DocumentType,
    ) -> AnalysisReport:
        """
        문서 분석 전체 파이프라인(LangGraph) 실행 (Async)

        Args:
            job_info (JobInfo): 채용 공고 정보
            document_text (str): 분석할 문서(이력서 또는 포트폴리오)의 텍스트
            doc_type (DocumentType): 문서 유형 (RESUME, PORTFOLIO). 분석 로직/프롬프트 분기에 사용.
        """
        ...
