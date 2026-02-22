import logging
from shared.db.connection import get_db
from shared.config import settings
from shared.schema.applicant import CompareRequest, CompareResponse

# Domain Interface
from .domain.interface.adapter_interfaces import ComparisonAnalyzer

# Application Service
from .application.services.comparison_use_case import ComparisonUseCase

# Infrastructure (Persistence)
from .infrastructure.persistence.candidate_repository import (
    SqlAlchemyCandidateRepository,
)
from .infrastructure.persistence.job_repository import SqlAlchemyJobRepository

# Infrastructure (Adapters)
from .infrastructure.adapters.llm.mock_agent import MockComparisonAnalyzer
from .infrastructure.adapters.llm.ai_agent.graph import LLMAnalyst


logger = logging.getLogger(__name__)


async def run_pipeline(request: CompareRequest) -> CompareResponse:
    """
    지원자 비교 파이프라인의 메인 진입점 (Async Entrypoint)
    외부(API Router 또는 pipeline_bridge)에서 호출할 때 이 함수를 사용합니다.

    Args:
        request: CompareRequest
            - job_posting_id: 비교 기준 공고 ID
            - user_id: 내 지원자 ID
            - competitor: 비교 대상 지원자 ID

    Returns:
        CompareResponse: 비교 결과 (comparison_metrics, strengths_report, weaknesses_report)
    """
    logger.info(
        f"🚀 [Pipeline Start] Comparing user {request.user_id} vs {request.competitor} "
        f"for job {request.job_posting_id}"
    )

    # DB 세션 라이프사이클 관리 (Async Generator)
    async for db_session in get_db():
        # 1. Infrastructure Layer 구현체 생성 (Dependencies)
        candidate_repo = SqlAlchemyCandidateRepository(db_session)
        job_repo = SqlAlchemyJobRepository(db_session)

        # 2. AI Analyzer 선택 (Mock or Real)
        analyzer: ComparisonAnalyzer

        # use_mock가 True인 경우 Mock Agent 사용
        if getattr(settings, "use_mock", False):
            logger.info("🤖 Using Mock Comparison Analyzer")
            analyzer = MockComparisonAnalyzer()
        else:
            analyzer: LLMAnalyst
            llm_provider = getattr(settings, "LLM_PROVIDER", "openai")
            if llm_provider == "gemini":
                model_name = getattr(settings, "GOOGLE_MODEL", "gemini-3-flash-preview")
            elif llm_provider == "vllm":
                model_name = getattr(settings, "VLLM_MODEL", "Qwen/Qwen3-32B-FP8")
            else:
                model_name = getattr(settings, "OPENAI_MODEL", "gpt-4o-mini")
            
            analyzer = LLMAnalyst(model_name=model_name, model_provider=llm_provider)

        # 3. Application Service에 의존성 주입 (Wiring)
        use_case = ComparisonUseCase(
            candidate_repo=candidate_repo,
            job_repo=job_repo,
            ai_analyzer=analyzer,
        )

        # 4. 비즈니스 로직 실행 (Async)
        result = await use_case.compare_candidates(
            my_candidate_id=int(request.user_id),
            competitor_candidate_id=int(request.competitor),
            job_posting_id=int(request.job_posting_id),
        )

        # 5. 트랜잭션 커밋 (읽기 전용이지만 일관성 유지)
        await db_session.commit()

        logger.info(
            f"✨ [Pipeline Complete] Comparison finished for user {request.user_id}"
        )
        return result

    raise RuntimeError("Failed to obtain database session")
