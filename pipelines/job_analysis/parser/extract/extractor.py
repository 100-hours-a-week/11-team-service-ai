import logging
from typing import Optional

from langchain_openai import ChatOpenAI
from langchain_core.runnables import Runnable

from shared.config import settings
from job_analysis.parser.extract.schemas import ExtractedJobData
from job_analysis.parser.extract.prompts import EXTRACTION_PROMPT

logger = logging.getLogger(__name__)


class JobPostingExtractor:
    def __init__(self, model_name: str = "gpt-4o"):
        """
        :param model_name: 사용할 모델명 (gpt-4o, gpt-3.5-turbo 등)
        """
        # 1. LLM 초기화
        # TODO: vLLM 사용 시 base_url과 api_key 수정 필요
        self.llm = ChatOpenAI(
            model=model_name,
            api_key=settings.OPENAI_API_KEY,
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
