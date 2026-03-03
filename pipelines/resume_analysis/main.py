import logging
from sqlalchemy.ext.asyncio import AsyncSession
from shared.db.connection import get_db


from shared.config import settings
from shared.schema.document import (
    ResumeAnalyzeRequest,
    ResumeAnalyzeResponse,
    PortfolioAnalyzeRequest,
    PortfolioAnalyzeResponse,
)

from .domain.models.document import DocumentType
from .domain.interface.adapter_interfaces import AnalystAgent

# Application Service
from .application.services.report import ApplicationAnalyzer

# Infrastructure (Persistence)
from .infrastructure.persistence.doc_repository import SqlAlchemyDocRepository
from .infrastructure.persistence.job_repository import SqlAlchemyJobRepository

# Infrastructure (Adapters)
from .infrastructure.adapters.storage.s3_storage import S3FileStorage
from .infrastructure.adapters.parser.pdf_extractor import PyPdfExtractor
from .infrastructure.adapters.llm.ai_agent.graph import LLMAnalyst
from .infrastructure.adapters.llm.mock_agent import MockAnalyst

logger = logging.getLogger(__name__)


async def run_resume_analysis(request: ResumeAnalyzeRequest) -> ResumeAnalyzeResponse:
    """
    이력서 분석 파이프라인 실행
    """
    target_doc_type = DocumentType.RESUME
    analyzer = None

    # --- [Step 1] 데이터 준비 (세션 1) ---
    async for session in get_db():
        analyzer = await _create_analyzer(session)
        job_info, target_text = await analyzer.prepare_analysis_data(
            user_id=int(request.user_id),
            job_id=int(request.job_posting_id),
            target_doc_type=target_doc_type,
        )
        # 이력서를 다운로드/추출했다면 상태가 변경되었을 수 있으므로 커밋
        await session.commit()
        break  # DB 세션 즉시 반납

    if not analyzer:
        raise RuntimeError("Failed to override analyzer from DB session")

    # --- [Step 2] AI 추론 대기 (DB 커넥션 없음) ---
    # DB 세션이 반환된 상태에서 느린 작업 진행
    report = await analyzer.run_ai_analysis(
        job_info=job_info,
        target_text=target_text,
        target_doc_type=target_doc_type,
    )

    # --- [Step 3] 최종 응답 포맷팅 반환 ---
    return analyzer.format_resume_response(report, int(request.user_id))


async def run_portfolio_analysis(
    request: PortfolioAnalyzeRequest,
) -> PortfolioAnalyzeResponse:
    """
    포트폴리오 분석 파이프라인 실행
    """
    target_doc_type = DocumentType.PORTFOLIO
    analyzer = None

    # --- [Step 1] 데이터 준비 (세션 1) ---
    async for session in get_db():
        analyzer = await _create_analyzer(session)
        job_info, target_text = await analyzer.prepare_analysis_data(
            user_id=int(request.user_id),
            job_id=int(request.job_posting_id),
            target_doc_type=target_doc_type,
        )
        await session.commit()
        break

    if not analyzer:
        raise RuntimeError("Failed to override analyzer from DB session")

    # --- [Step 2] AI 추론 대기 (DB 커넥션 없음) ---
    report = await analyzer.run_ai_analysis(
        job_info=job_info,
        target_text=target_text,
        target_doc_type=target_doc_type,
    )

    # --- [Step 3] 최종 응답 포맷팅 반환 ---
    return analyzer.format_portfolio_response(report, int(request.user_id))


async def _create_analyzer(session: AsyncSession) -> ApplicationAnalyzer:
    """
    ApplicationAnalyzer 인스턴스 생성 및 의존성 주입
    """
    # 1. LLM & Agent
    agent: AnalystAgent

    # settings.use_mock가 True인 경우 Mock Agent 사용
    if getattr(settings, "use_mock", False):
        logger.info("🤖 Initializing Mock Analyst Agent")
        agent = MockAnalyst()
    else:
        # LLM 설정을 문자열로 전달 (Runtime Loading)
        llm_provider = getattr(settings, "LLM_PROVIDER", "openai")

        if llm_provider == "gemini":
            model_name = getattr(settings, "GOOGLE_MODEL", "gemini-1.5-flash")
            logger.info(f"🤖 Initializing Analyst Agent with Gemini ({model_name})")
        elif llm_provider == "vllm":
            model_name = getattr(settings, "VLLM_MODEL", "Qwen/Qwen3-32B-FP8")
            logger.info(f"🤖 Initializing Analyst Agent with vLLM ({model_name})")
        else:
            model_name = getattr(settings, "OPENAI_MODEL", "gpt-4o")
            logger.info(f"🤖 Initializing Analyst Agent with OpenAI ({model_name})")

        # LLMAnalyst 초기화 (객체 대신 설정값 전달)
        agent = LLMAnalyst(model_name=model_name, model_provider=llm_provider)

    # 2. Infrastructure Adapters
    job_repo = SqlAlchemyJobRepository(session)
    doc_repo = SqlAlchemyDocRepository(session)
    file_storage = S3FileStorage()
    extractor = PyPdfExtractor()

    # 3. Service Assembly
    return ApplicationAnalyzer(
        job_repo=job_repo,
        doc_repo=doc_repo,
        file_storage=file_storage,
        extractor=extractor,
        agent=agent,
    )
