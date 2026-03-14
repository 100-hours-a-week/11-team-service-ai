"""Shared utility functions used in the project.

Functions:
    load_chat_model: Load a chat model based on provider and name.
"""

import logging

from langchain_core.language_models import BaseChatModel
from shared.config import settings
from typing import Optional, Any
from pydantic import BaseModel, Field
from shared.schema.common_schema import ApiResponse

logger = logging.getLogger(__name__)


class AiResponse(BaseModel):
    """응답결과 정형화"""

    response: str = Field(description="응답결과")


def load_chat_model(model_name: str, model_provider: str) -> BaseChatModel:
    """Load a chat model based on the provider and name."""

    if model_provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        logger.info(f"🤖 Loading Gemini Model: {model_name}")
        return ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0,
        )
    elif model_provider == "vllm":
        from langchain_openai import ChatOpenAI
        from pydantic import SecretStr

        logger.info(f"🤖 Loading vLLM Model: {model_name}")

        return ChatOpenAI(
            model=model_name,
            api_key=SecretStr(
                "EMPTY"
            ),  # vLLM은 기본적으로 api key를 요구하지 않으므로 더미값을 사용합니다.
            base_url=settings.VLLM_BASE_URL,
            temperature=0,
            # max_tokens=1024, # 필요에 따라 설정
        )
    else:  # openai or default
        from langchain_openai import ChatOpenAI
        from pydantic import SecretStr

        logger.info(f"🤖 Loading OpenAI Model: {model_name}")
        return ChatOpenAI(
            model=model_name,
            temperature=0,
            api_key=(
                SecretStr(settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
            ),
        )


async def send_eval_job_callback(
    eval_job_id: Optional[str],
    success: bool = True,
    data: Optional[dict[str, Any]] = None,
) -> None:
    """eval_job_id가 존재할 경우 스프링 서버(콜백 API)로 결과를 전송합니다."""
    if not eval_job_id:
        return

    import httpx

    url = settings.MQ_CALLBACK_URL
    if not url:
        logger.warning("MQ_CALLBACK_URL is not set in environment variables.")
        return

    api_response = ApiResponse(eval_job_id=eval_job_id, success=success, data=data)

    payload = api_response.model_dump(mode="json", exclude_none=True)

    try:
        async with httpx.AsyncClient(verify=False) as client:
            response = await client.post(url, json=payload, timeout=10.0)
            response.raise_for_status()
            logger.info(f"✅ Callback sent successfully for eval_job_id: {eval_job_id}")
    except Exception as e:
        logger.error(f"❌ Failed to send callback for eval_job_id {eval_job_id}: {e}")
