from typing import Protocol, List
from ..models.job import EvaluationCriteria, JobInfo
from ..models.evaluation import CompetencyResult, OverallFeedback

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
    async def evaluate_competency(
        self, 
        job_info: JobInfo,
        criteria: EvaluationCriteria, 
        resume_text: str, 
        portfolio_text: str
    ) -> CompetencyResult:
        """단일 평가 기준 분석 (Async)"""
        ...

    async def synthesize_report(
        self, 
        job_info: JobInfo,
        competency_results: List[CompetencyResult]
    ) -> OverallFeedback:
        """종합 리포트 생성 (Async)"""
        ...
