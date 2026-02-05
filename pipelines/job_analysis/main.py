import logging

from shared.schema.job_posting import (
    JobPostingAnalyzeRequest,
    JobPostingAnalyzeResponse,
    JobPostingDeleteResponse,
)
from .application.services.extraction_service import JobExtractionService
from .infrastructure.adapters.crawling.router import DynamicRoutingCrawler
from .infrastructure.adapters.llm.job_extractor import LLMJobExtractor

from shared.config import settings
from .infrastructure.adapters.llm.mock_extractor import MockJobExtractor

logger = logging.getLogger(__name__)


# TODO: 공고분석 파이프라인 구현, 벡터db에만 공고 저장
async def run_pipeline(request: JobPostingAnalyzeRequest) -> JobPostingAnalyzeResponse:
    """
    크롤링 및 추출 파이프라인
    """
    # 설정에 따라 Extractor 주입 결정
    extractor_impl = None
    if settings.use_mock:
        extractor_impl = MockJobExtractor()
    else:
        llm_model = None
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
        
        extractor_impl = LLMJobExtractor(llm=llm_model)

    service = JobExtractionService(
        crawler=DynamicRoutingCrawler(), extractor=extractor_impl
    )
    return await service.extract_job_data(request.url)


# TODO: 삭제 파이프라인 구현, 벡터db에 저장된 내용만 삭제
async def delete_pipeline(job_posting_id: int) -> JobPostingDeleteResponse:
    """
    Job Posting Deletion Pipeline Entrypoint
    """
    logger.info(f"🚀 [Pipeline Start] Delete Job Posting ID: {job_posting_id}")
    return JobPostingDeleteResponse(deleted_id=job_posting_id)
