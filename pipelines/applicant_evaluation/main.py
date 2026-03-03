import logging
from shared.db.connection import get_db
from .infrastructure.persistence.job_repository import SqlAlchemyJobRepository
from .infrastructure.persistence.doc_repository import SqlAlchemyDocRepository
from shared.config import settings
from shared.utils import load_chat_model
from .infrastructure.adapters.llm.ai_agent import LLMAnalyst
from .infrastructure.adapters.llm.mock_agent import MockAnalyst
from .domain.interface.adapter_interfaces import AnalystAgent
from .infrastructure.adapters.storage.s3_storage import S3FileStorage
from .infrastructure.adapters.parser.pdf_extractor import PyPdfExtractor
from .application.services.analyzer import ApplicationAnalyzer
from shared.schema.applicant import EvaluateRequest, EvaluateResponse

logger = logging.getLogger(__name__)


async def run_pipeline(request: EvaluateRequest) -> EvaluateResponse:
    """
    지원자 평가 파이프라인의 메인 진입점 (Async Entrypoint)
    외부(API Router)에서 호출할 때 이 함수를 사용합니다.
    """
    user_id = int(request.user_id)
    job_id = int(request.job_posting_id)
    analyzer = None

    # --- [Step 1] 데이터 준비 (세션 1) ---
    async for db_session in get_db():
        analyzer = await _create_analyzer(db_session)
        job_info, resume_text, portfolio_text = await analyzer.prepare_evaluation_data(
            user_id=user_id, job_id=job_id
        )
        # 서류 추출 등으로 인한 DB 변경사항 커밋
        await db_session.commit()
        break  # DB 세션 즉시 반납

    if not analyzer:
        raise RuntimeError("Failed to obtain database session")

    # --- [Step 2] AI 추론 대기 (DB 커넥션 없음) ---
    # DB 세션이 반환된 상태에서 느린 작업 진행
    report = await analyzer.run_ai_evaluation(
        job_info=job_info,
        resume_text=resume_text,
        portfolio_text=portfolio_text,
        user_id=user_id,
    )

    # --- [Step 3] 최종 응답 포맷팅 반환 ---
    # DB 세션 없이 반환 수행
    return analyzer.format_response(report=report, user_id=user_id, job_id=job_id)


async def _create_analyzer(db_session) -> ApplicationAnalyzer:
    job_repo = SqlAlchemyJobRepository(db_session)
    doc_repo = SqlAlchemyDocRepository(db_session)

    file_storage = S3FileStorage()
    extractor = PyPdfExtractor()

    agent: AnalystAgent
    if getattr(settings, "use_mock", False):
        agent = MockAnalyst()
    else:
        model_provider = getattr(settings, "LLM_PROVIDER", "openai")
        if model_provider == "gemini":
            model_name = getattr(settings, "GOOGLE_MODEL", "gemini-3-flash-preview")
        elif model_provider == "vllm":
            model_name = getattr(settings, "VLLM_MODEL", "Qwen/Qwen3-32B-FP8")
        else:
            model_name = getattr(settings, "OPENAI_MODEL", "gpt-4o-mini")

        llm_model = load_chat_model(
            model_name=model_name, model_provider=model_provider
        )
        agent = LLMAnalyst(llm=llm_model)

    return ApplicationAnalyzer(
        job_repo=job_repo,
        doc_repo=doc_repo,
        file_storage=file_storage,
        extractor=extractor,
        agent=agent,
    )
