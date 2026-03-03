from typing import Protocol, Tuple
from ..models.candidate import Candidate
from ..models.job import JobInfo


class ComparisonAnalyzer(Protocol):
    """
    지원자 비교 분석 AI 인터페이스 (Async)
    두 지원자의 역량을 대조하여 강점/약점 분석
    """

    async def analyze_candidates(
        self,
        my_candidate: Candidate,
        competitor_candidate: Candidate,
        job_info: JobInfo,
    ) -> Tuple[str, str]:
        """
        AI(LLM)를 활용해 두 지원자를 비교 분석

        Args:
            my_candidate: 내 지원자 (선택한 지원자)
            competitor_candidate: 비교 대상 지원자
            job_info: 비교 기준이 되는 채용 공고 정보

        Returns:
            Tuple[str, str]: (강점 리포트, 약점 리포트)
                - 강점: 내 지원자가 상대 대비 우수한 점
                - 약점: 내 지원자가 상대 대비 부족한 점
        """
        ...
