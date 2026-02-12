import logging
from shared.schema.applicant import CompareResponse
from ...domain.interface.adapter_interfaces import ComparisonAnalyzer
from ...domain.interface.repository_interfaces import (
    CandidateRepository,
    JobRepository,
)
from ...domain.services.comparison_service import CandidateComparisonService
from .mapper import ComparisonMapper

logger = logging.getLogger(__name__)


class ComparisonUseCase:
    """
    지원자 비교 유스케이스 (Application Service)
    Repository, AI Analyzer를 조율하여 비교 리포트 생성
    """

    def __init__(
        self,
        candidate_repo: CandidateRepository,
        job_repo: JobRepository,
        ai_analyzer: ComparisonAnalyzer,
    ):
        self.candidate_repo = candidate_repo
        self.job_repo = job_repo
        self.ai_analyzer = ai_analyzer

    async def compare_candidates(
        self,
        my_candidate_id: str,
        competitor_candidate_id: str,
        job_posting_id: str,
    ) -> CompareResponse:
        """
        두 지원자를 비교하여 리포트 생성

        Args:
            my_candidate_id: 내 지원자 ID
            competitor_candidate_id: 비교 대상 지원자 ID
            job_posting_id: 공고 ID

        Returns:
            CompareResponse: 비교 결과 응답 스키마

        Raises:
            ValueError: 지원자 또는 공고를 찾을 수 없는 경우
        """
        logger.info(
            f"🚀 [Comparison Start] My: {my_candidate_id}, "
            f"Competitor: {competitor_candidate_id}, Job: {job_posting_id}"
        )

        # 1. 데이터 조회 (Repository)
        my_candidate = await self.candidate_repo.find_candidate(
            my_candidate_id, job_posting_id
        )
        if not my_candidate:
            logger.error(f"❌ My candidate not found: {my_candidate_id}")
            raise ValueError(f"Candidate not found: {my_candidate_id}")

        competitor_candidate = await self.candidate_repo.find_candidate(
            competitor_candidate_id, job_posting_id
        )
        if not competitor_candidate:
            logger.error(f"❌ Competitor candidate not found: {competitor_candidate_id}")
            raise ValueError(f"Candidate not found: {competitor_candidate_id}")

        job_info = await self.job_repo.find_job(job_posting_id)
        if not job_info:
            logger.error(f"❌ Job not found: {job_posting_id}")
            raise ValueError(f"Job not found: {job_posting_id}")

        logger.info("✅ Data retrieval complete")


        # 2. AI 분석 호출 (Infrastructure Adapter)
        logger.info("🤖 Starting AI comparison analysis...")
        strengths, weaknesses = await self.ai_analyzer.analyze_candidates(
            my_candidate, competitor_candidate, job_info
        )
        logger.info("✅ AI analysis complete")

        # 4. 비교 리포트 생성 (Domain Service)
        logger.info("📊 Generating comparison report...")
        report = CandidateComparisonService.generate_comparison_report(
            my_candidate, competitor_candidate, strengths, weaknesses
        )

        # 5. 도메인 모델을 API 응답 스키마로 변환 (Mapper)
        logger.info("🔄 Converting to API response schema...")
        response = ComparisonMapper.to_compare_response(report)

        logger.info(
            f"✨ [Comparison Complete] My: {my_candidate_id}, "
            f"Competitor: {competitor_candidate_id}"
        )
        return response
