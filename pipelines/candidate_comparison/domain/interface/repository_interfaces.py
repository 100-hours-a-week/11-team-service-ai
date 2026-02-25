from typing import Optional, Protocol

from ..models.candidate import Candidate
from ..models.job import JobInfo


class CandidateRepository(Protocol):
    """
    지원자 애그리거트 저장소 인터페이스 (Async)
    """

    async def find_candidate(
        self, candidate_id: str, job_posting_id: str
    ) -> Optional[Candidate]:
        """
        지원자 정보, 서류, 평가 결과를 포함한 애그리거트 조회

        Args:
            candidate_id: 지원자 고유 ID
            job_posting_id: 공고 ID

        Returns:
            Candidate: 지원자 애그리거트 (서류 + 평가 결과 포함)
        """
        ...


class JobRepository(Protocol):
    """
    채용 공고 관련 데이터 저장소 인터페이스 (Async)
    """

    async def find_job(self, job_posting_id: str) -> Optional[JobInfo]:
        """
        비교의 기준이 되는 공고의 요구사항 및 직무 기술서 조회

        Args:
            job_posting_id: 공고 고유 ID

        Returns:
            JobInfo: 채용 공고 정보 (평가 기준 포함)
        """
        ...
