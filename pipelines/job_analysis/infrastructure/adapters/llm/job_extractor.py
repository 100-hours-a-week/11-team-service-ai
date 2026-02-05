import logging
from typing import Optional
from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import PydanticOutputParser
from ....domain.interface.extractor import JobDataExtractor
from ....domain.models.job_data import ExtractedJobData
from .prompts import get_job_extraction_prompt

logger = logging.getLogger(__name__)


class LLMJobExtractor(JobDataExtractor):
    """
    LLM(LangChain)을 사용하여 텍스트에서 채용 공고 데이터를 추출하는 어댑터.
    특정 LLM 구현체에 의존하지 않고 BaseChatModel을 주입받아 사용합니다.
    """

    def __init__(self, llm: BaseChatModel):
        self.llm = llm

        # Pydantic 모델을 사용하여 파서 설정
        self.parser = PydanticOutputParser(pydantic_object=ExtractedJobData)

    async def extract(self, raw_text: str) -> Optional[ExtractedJobData]:
        """
        raw_text에서 구조화된 데이터를 추출하여 ExtractedJobData 반환
        """
        logger.info(f"🧠 Extracting job data from text ({len(raw_text)} chars)...")

        try:
            # 프롬프트 정의
            prompt = get_job_extraction_prompt()

            # 체인 연결
            chain = prompt | self.llm | self.parser

            # 실행
            result = await chain.ainvoke(
                {
                    "raw_text": raw_text[:15000],  # 토큰 제한 고려하여 절삭
                    # "format_instructions": self.parser.get_format_instructions(), # Removed
                }
            )

            # PydanticOutputParser는 이미 Pydantic 객체를 반환하므로 바로 리턴
            logger.info(
                f"✅ Job extraction successful: {result.job_title} at {result.company_name}"
            )
            return result

        except Exception as e:
            logger.error(f"❌ Extraction failed: {e}", exc_info=True)
            return None
