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

from shared.pipeline_bridge.broker import broker_compare
from shared.pipeline_bridge.constants import TASK_CANDIDATE_COMPARE

logger = logging.getLogger(__name__)


@broker_compare.task(task_name=TASK_CANDIDATE_COMPARE)
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

    use_case = None

    # --- [Step 1] 데이터 준비 (세션 1) ---
    async for db_session in get_db():
        use_case = _create_use_case(db_session)
        my_candidate, competitor_candidate, job_info = (
            await use_case.prepare_comparison_data(
                my_candidate_id=str(request.user_id),
                competitor_candidate_id=str(request.competitor),
                job_posting_id=str(request.job_posting_id),
            )
        )
        await db_session.commit()
        break

    if not use_case:
        raise RuntimeError("Failed to obtain database session")

    # --- [Step 2] AI 분석 (DB 연결 불필요) ---
    strengths, weaknesses = await use_case.run_ai_comparison(
        my_candidate=my_candidate,
        competitor_candidate=competitor_candidate,
        job_info=job_info,
    )

    # --- [Step 3] 최종 응답 포맷팅 및 반환 (DB 연결 불필요) ---
    result = use_case.format_comparison_response(
        my_candidate=my_candidate,
        competitor_candidate=competitor_candidate,
        strengths=strengths,
        weaknesses=weaknesses,
    )

    logger.info(
        f"✨ [Pipeline Complete] Comparison finished for user {request.user_id}"
    )
    return result


def _create_use_case(db_session) -> ComparisonUseCase:
    candidate_repo = SqlAlchemyCandidateRepository(db_session)
    job_repo = SqlAlchemyJobRepository(db_session)

    analyzer: ComparisonAnalyzer

    if getattr(settings, "use_mock", False):
        logger.info("🤖 Using Mock Comparison Analyzer")
        analyzer = MockComparisonAnalyzer()
    else:
        llm_provider = getattr(settings, "LLM_PROVIDER", "openai")
        if llm_provider == "gemini":
            model_name = getattr(settings, "GOOGLE_MODEL", "gemini-3-flash-preview")
        elif llm_provider == "vllm":
            model_name = getattr(settings, "VLLM_MODEL", "Qwen/Qwen3-32B-FP8")
        else:
            model_name = getattr(settings, "OPENAI_MODEL", "gpt-4o-mini")

        analyzer = LLMAnalyst(model_name=model_name, model_provider=llm_provider)

    return ComparisonUseCase(
        candidate_repo=candidate_repo,
        job_repo=job_repo,
        ai_analyzer=analyzer,
    )
