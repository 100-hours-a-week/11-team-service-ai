from typing import Protocol, Optional
from ..models.job import JobInfo
from ..models.document import ApplicantDocuments, ParsedDoc
from ..models.report import AnalysisReport

class JobRepository(Protocol):
    """
    채용 공고 관련 데이터 저장소 인터페이스 (Async)
    """
    async def get_job_info(self, job_id: int) -> Optional[JobInfo]:
        """job_id로 채용 공고의 핵심 정보 및 평가 기준을 조회"""
        ...

class DocRepository(Protocol):
    """
    지원 서류(이력서, 포트폴리오) 관련 데이터 저장소 인터페이스 (Async)
    """
    async def get_documents(self, user_id: int, job_id: int) -> ApplicantDocuments:
        """
        특정 지원자의 전체 제출 서류 상태를 조회 (Aggregate Root 반환)
        """
        ...

    async def save_parsed_doc(
        self, 
        user_id: int, 
        job_id: int, 
        parsed_doc: ParsedDoc
    ) -> None:
        """
        새로 추출한 텍스트 데이터를 저장
        """
        ...
