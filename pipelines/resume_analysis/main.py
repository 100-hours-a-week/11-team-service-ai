import logging
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.language_models import BaseChatModel
from shared.db.connection import get_db


from shared.config import settings
from shared.schema.document import (
    ResumeAnalyzeRequest, 
    ResumeAnalyzeResponse,
    PortfolioAnalyzeRequest,
    PortfolioAnalyzeResponse
)

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

async def run_resume_analysis(
    request: ResumeAnalyzeRequest
) -> ResumeAnalyzeResponse:
    """
    이력서 분석 파이프라인 실행
    """
    async for session in get_db():
        analyzer = await _create_analyzer(session)
        
        result = await analyzer.analyze_resume(
            user_id=int(request.user_id),
            job_id=int(request.job_posting_id)
        )
        
        # 성공 시 커밋 (데이터 지속성 보장)
        await session.commit()
        return result
    
    raise RuntimeError("Failed to get DB session")

async def run_portfolio_analysis(
    request: PortfolioAnalyzeRequest
) -> PortfolioAnalyzeResponse:
    """
    포트폴리오 분석 파이프라인 실행
    """
    async for session in get_db():
        analyzer = await _create_analyzer(session)

        result = await analyzer.analyze_portfolio(
            user_id=int(request.user_id),
            job_id=int(request.job_posting_id)
        )
        
        # 성공 시 커밋
        await session.commit()
        return result

    raise RuntimeError("Failed to get DB session")

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
            # Gemini provider string adjustment if needed (e.g. 'google_genai')
            # load_chat_model in utils.py handles 'google_genai' for Gemini
            agent_provider = "gemini" 
        else:
            model_name = getattr(settings, "OPENAI_MODEL", "gpt-4o")
            logger.info(f"🤖 Initializing Analyst Agent with OpenAI ({model_name})")
            agent_provider = "openai"

        # LLMAnalyst 초기화 (객체 대신 설정값 전달)
        agent = LLMAnalyst(model_name=model_name, model_provider=agent_provider)

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
