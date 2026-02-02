import logging
from typing import Optional

from langchain_openai import ChatOpenAI
from langchain_core.runnables import Runnable

from shared.config import settings
from job_analysis.parser.extract.schemas import ExtractedJobData
from job_analysis.parser.extract.prompts import EXTRACTION_PROMPT

from pydantic import SecretStr

logger = logging.getLogger(__name__)


class JobPostingExtractor:
    def __init__(self, model_name: str = "gpt-4o"):
        """
        :param model_name: 사용할 모델명 (gpt-4o, gpt-3.5-turbo 등)
        """
        if not settings.use_mock:
            # 1. LLM 초기화
            # TODO: vLLM 사용 시 base_url과 api_key 수정 필요
            self.llm = ChatOpenAI(
                model=model_name,
                api_key=(
                    SecretStr(settings.OPENAI_API_KEY)
                    if settings.OPENAI_API_KEY
                    else None
                ),
                temperature=0,  # 추출 작업이므로 낮은 온도 설정
            )

            # 2. 구조화된 출력을 위한 LLM 설정 (Tool Calling)
            structured_llm = self.llm.with_structured_output(ExtractedJobData)

            # 3. Prompt + LLM 체인 구성
            self.chain: Runnable = EXTRACTION_PROMPT | structured_llm

    async def extract(self, text: str) -> Optional[ExtractedJobData]:
        """
        채용 공고 텍스트에서 정보를 추출하여 구조화된 데이터로 반환합니다.
        """
        # Mock 모드: OpenAI 호출 없이 목업 데이터 반환
        if settings.use_mock:
            logger.info("[Mock] JobPostingExtractor.extract")
            return ExtractedJobData(
                company_name="[Mock] 테스트 회사",
                job_title="[Mock] 백엔드 개발자",
                main_tasks=[
                    "API 설계 및 개발",
                    "데이터베이스 설계",
                    "시스템 아키텍처 구축",
                ],
                requirements=["Python 3년 이상", "FastAPI 경험"],
                preferred=["AWS 경험", "Docker/Kubernetes 경험"],
                tech_stacks=["Python", "FastAPI", "PostgreSQL", "Docker"],
                start_date=None,
                end_date=None,
                ai_summary="[Mock] 이 공고는 백엔드 개발자를 찾고 있습니다.",
                evaluation_criteria=[
                    {
                        "name": "기술역량",
                        "description": "Python, FastAPI 등 기술 스택 숙련도",
                    },
                    {"name": "프로젝트경험", "description": "관련 프로젝트 수행 경험"},
                ],
            )
        if not text or len(text.strip()) < 50:
            logger.warning("Empty or too short text provided for extraction.")
            return None

        try:
            # 텍스트 길이 제한 (토큰 비용 절감 및 Context Limit 방지)
            # 만약 텍스트가 너무 길면 앞뒤를 자르거나 요약하는 전처리가 필요할 수 있음
            # 현재는 단순히 로그만 남김
            if len(text) > 20000:
                logger.warning(
                    f"Text is very long ({len(text)} chars). Truncating may be needed."
                )

            logger.info("waiting llm extract response...")
            # 비동기 호출
            result: ExtractedJobData = await self.chain.ainvoke({"text": text})
            logger.info(f"✅ Extraction successful for: {result.company_name}")
            return result

        except Exception as e:
            logger.error(f"❌ Extraction failed: {e}", exc_info=True)
            return None
