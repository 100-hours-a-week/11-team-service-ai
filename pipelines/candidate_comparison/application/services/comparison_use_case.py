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

    async def prepare_comparison_data(
        self,
        my_candidate_id: str,
        competitor_candidate_id: str,
        job_posting_id: str,
    ):
        """
        [Step 1] 데이터 준비 (DB 세션 필요)
        """
        logger.info(
            f"🚀 [Comparison Start] My: {my_candidate_id}, "
            f"Competitor: {competitor_candidate_id}, Job: {job_posting_id}"
        )

        # 1. 데이터 조회 (Repository)
        my_candidate = await self.candidate_repo.find_candidate(
            my_candidate_id, job_posting_id
        )
        if not my_candidate or not my_candidate.is_ready_for_comparison():
            logger.error(f"❌ My candidate not found or not ready: {my_candidate_id}")
            raise ValueError(f"Candidate not found or not ready: {my_candidate_id}")

        competitor_candidate = await self.candidate_repo.find_candidate(
            competitor_candidate_id, job_posting_id
        )
        if (
            not competitor_candidate
            or not competitor_candidate.is_ready_for_comparison()
        ):
            logger.error(
                f"❌ Competitor candidate not found or not ready: {competitor_candidate_id}"
            )
            raise ValueError(
                f"Candidate not found or not ready: {competitor_candidate_id}"
            )

        job_info = await self.job_repo.find_job(job_posting_id)
        if not job_info:
            logger.error(f"❌ Job not found: {job_posting_id}")
            raise ValueError(f"Job not found: {job_posting_id}")

        logger.info("✅ Data retrieval complete")
        return my_candidate, competitor_candidate, job_info

    async def run_ai_comparison(self, my_candidate, competitor_candidate, job_info):
        """
        [Step 2] AI 분석 호출 (DB 세션 불필요)
        """
        logger.info("🤖 Starting AI comparison analysis...")
        strengths, weaknesses = await self.ai_analyzer.analyze_candidates(
            my_candidate, competitor_candidate, job_info
        )
        logger.info("✅ AI analysis complete")
        return strengths, weaknesses

    def format_comparison_response(
        self, my_candidate, competitor_candidate, strengths, weaknesses
    ) -> CompareResponse:
        """
        [Step 3] 비교 리포트 생성 및 DTO 반환 (DB 세션 불필요)
        """
        logger.info("📊 Generating comparison report...")
        report = CandidateComparisonService.generate_comparison_report(
            my_candidate, competitor_candidate, strengths, weaknesses
        )

        logger.info("🔄 Converting to API response schema...")
        response = ComparisonMapper.to_compare_response(report)

        return response
