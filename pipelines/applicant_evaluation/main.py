import logging
from shared.db.connection import get_db
from .infrastructure.persistence.job_repository import SqlAlchemyJobRepository
from .infrastructure.persistence.doc_repository import SqlAlchemyDocRepository
from shared.config import settings
from .infrastructure.adapters.llm.openai_agent import LLMAnalyst
from .infrastructure.adapters.llm.mock_agent import MockAnalyst
from .domain.interface.adapter_interfaces import AnalystAgent
from .infrastructure.adapters.storage.s3_storage import S3FileStorage
from .infrastructure.adapters.parser.pdf_extractor import PyPdfExtractor
from .application.services.analyzer import ApplicationAnalyzer
from shared.schema.applicant import EvaluateRequest, EvaluateResponse
from langchain_core.language_models import BaseChatModel

logger = logging.getLogger(__name__)


async def run_pipeline(request: EvaluateRequest) -> EvaluateResponse:
    """
    지원자 평가 파이프라인의 메인 진입점 (Async Entrypoint)
    외부(API Router)에서 호출할 때 이 함수를 사용합니다.
    """
    # DB 세션 라이프사이클 관리 (Async Generator)
    async for db_session in get_db():
        # 1. Infrastructure Layer의 구현체 생성 (Dependencies)
        job_repo = SqlAlchemyJobRepository(db_session)
        doc_repo = SqlAlchemyDocRepository(db_session)

        file_storage = S3FileStorage()
        extractor = PyPdfExtractor()

        # External Clients (DI) & Mock Selection
        # use_mock 프로퍼티가 있다면 그것을 사용 (dev profile 체크 포함됨)
        # 또는 settings.USE_MOCK을 직접 사용해도 됨
        agent: AnalystAgent
        if getattr(settings, "use_mock", False):
            agent = MockAnalyst()
        else:
            llm_model: BaseChatModel
            if getattr(settings, "LLM_PROVIDER", "openai") == "gemini":
                from langchain_google_genai import ChatGoogleGenerativeAI

                model = getattr(settings, "GOOGLE_MODEL", "gemini-3-flash-preview")
                logger.info(f"🤖 Initializing LLMJobExtractor with gemini ({model})")

                llm_model = ChatGoogleGenerativeAI(
                    model=model,
                    google_api_key=settings.GOOGLE_API_KEY,
                    temperature=0,
                )
            else:
                from langchain_openai import ChatOpenAI
                from pydantic import SecretStr

                model = getattr(settings, "OPENAI_MODEL", "gpt-4o-mini")
                logger.info(f"🤖 Initializing LLMJobExtractor with OpenAI ({model})")

                llm_model = ChatOpenAI(
                    model=model,
                    temperature=0,
                    api_key=(
                        SecretStr(settings.OPENAI_API_KEY)
                        if settings.OPENAI_API_KEY
                        else None
                    ),
                    model_kwargs={"response_format": {"type": "json_object"}},
                )
            agent = LLMAnalyst(llm=llm_model)

        # 2. Application Layer 서비스에 의존성 주입 (Wiring)
        analyzer = ApplicationAnalyzer(
            job_repo=job_repo,
            doc_repo=doc_repo,
            file_storage=file_storage,
            extractor=extractor,
            agent=agent,
        )

        # 3. 비즈니스 로직 실행 (Async)
        # 서비스 계층의 run 메서드도 async여야 함
        result = await analyzer.run(int(request.user_id), int(request.job_posting_id))

        # 4. 트랜잭션 커밋 (저장소 변경사항 반영)
        await db_session.commit()

        return result

    raise RuntimeError("Failed to obtain database session")
