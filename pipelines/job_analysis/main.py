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
from shared.utils import load_chat_model, send_eval_job_callback

from .infrastructure.adapters.llm.mock_extractor import MockJobExtractor

from langchain_core.language_models import BaseChatModel
from .domain.interface.extractor import JobDataExtractor

from shared.pipeline_bridge.broker import broker_job
from shared.pipeline_bridge.constants import TASK_JOB_ANALYZE, TASK_JOB_DELETE

logger = logging.getLogger(__name__)


# TODO: 공고분석 파이프라인 구현, 벡터db에만 공고 저장
@broker_job.task(task_name=TASK_JOB_ANALYZE)
async def run_pipeline(request: JobPostingAnalyzeRequest) -> JobPostingAnalyzeResponse:
    """
    크롤링 및 추출 파이프라인
    """
    # 설정에 따라 Extractor 주입 결정
    extractor_impl: JobDataExtractor
    if settings.use_mock:
        extractor_impl = MockJobExtractor()
    else:
        llm_model: BaseChatModel
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

        extractor_impl = LLMJobExtractor(llm=llm_model)

    service = JobExtractionService(
        crawler=DynamicRoutingCrawler(), extractor=extractor_impl
    )
    result = await service.extract_job_data(request.url)

    if getattr(request, "evalJobId", None):
        await send_eval_job_callback(
            eval_job_id=request.evalJobId, success=True, data=result.model_dump()
        )

    return result


# TODO: 삭제 파이프라인 구현, 벡터db에 저장된 내용만 삭제
@broker_job.task(task_name=TASK_JOB_DELETE)
async def delete_pipeline(job_posting_id: int) -> JobPostingDeleteResponse:
    """
    Job Posting Deletion Pipeline Entrypoint
    """
    logger.info(f"🚀 [Pipeline Start] Delete Job Posting ID: {job_posting_id}")
    return JobPostingDeleteResponse(deleted_id=job_posting_id)
