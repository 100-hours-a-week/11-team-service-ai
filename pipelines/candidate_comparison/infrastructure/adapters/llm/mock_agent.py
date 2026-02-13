import logging
from typing import Tuple

from ....domain.interface.adapter_interfaces import ComparisonAnalyzer
from ....domain.models.candidate import Candidate
from ....domain.models.job import JobInfo

logger = logging.getLogger(__name__)


class MockComparisonAnalyzer(ComparisonAnalyzer):
    """
    개발 및 테스트용 Mock Comparison Agent
    실제 LLM 호출 없이 고정된 더미 비교 분석 데이터를 반환합니다.
    """

    async def analyze_candidates(
        self,
        my_candidate: Candidate,
        competitor_candidate: Candidate,
        job_info: JobInfo,
    ) -> Tuple[str, str]:
        """
        두 지원자를 비교 분석하여 강점/약점 리포트 반환

        Args:
            my_candidate: 내 지원자
            competitor_candidate: 비교 대상 지원자
            job_info: 공고 정보

        Returns:
            (강점 리포트, 약점 리포트)
        """
        logger.info(
            f"[Mock] analyze_candidates called for job: {job_info.company_name}"
        )

        # 점수 기반 간단 비교 로직
        my_score = my_candidate.evaluation.overall_score
        competitor_score = competitor_candidate.evaluation.overall_score

        # Mock 강점 리포트 생성
        if my_score > competitor_score:
            strengths = (
                f"[Mock] {job_info.company_name} 공고 기준으로 종합 점수가 "
                f"{my_score - competitor_score:.1f}점 더 높습니다. "
                f"특히 기술 스택 숙련도와 업무 경력에서 우수한 평가를 받았습니다."
            )
        elif my_score == competitor_score:
            strengths = (
                f"[Mock] {job_info.company_name} 공고 기준으로 종합 점수가 비슷합니다. "
                f"특정 역량에서는 비교 우위를 가지고 있습니다."
            )
        else:
            strengths = (
                f"[Mock] {job_info.company_name} 공고 기준으로 일부 역량에서 강점을 보입니다. "
                f"특히 문서화 능력과 커뮤니케이션 스킬이 돋보입니다."
            )

        # Mock 약점 리포트 생성
        if my_score < competitor_score:
            weaknesses = (
                f"[Mock] 비교 대상 지원자 대비 종합 점수가 "
                f"{competitor_score - my_score:.1f}점 낮습니다. "
                f"특히 대규모 프로젝트 경험과 오픈소스 기여도 측면에서 보완이 필요합니다."
            )
        elif my_score == competitor_score:
            weaknesses = (
                f"[Mock] 전반적으로 유사한 수준이나, "
                f"특정 기술 스택(예: {', '.join(job_info.tech_stacks[:2])})에 대한 "
                f"실무 경험을 더 강화하면 경쟁력을 높일 수 있습니다."
            )
        else:
            weaknesses = (
                f"[Mock] 전반적으로 우수하나, "
                f"지속적인 학습과 최신 기술 트렌드 파악을 통해 "
                f"경쟁 우위를 더욱 공고히 할 수 있습니다."
            )

        logger.info("[Mock] Comparison analysis completed")
        return (strengths, weaknesses)
