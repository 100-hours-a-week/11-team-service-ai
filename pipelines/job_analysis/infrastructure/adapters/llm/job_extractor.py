import logging
from typing import Optional
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from ....domain.interface.extractor import JobDataExtractor
from ....domain.models.job_data import ExtractedJobData

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
            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        """
                당신은 채용 공고 분석 전문가입니다. 주어진 채용 공고 텍스트에서 핵심 정보를 추출하여 JSON 형식으로 출력하세요.
                
                추출해야 할 정보:
                1. company_name: 회사명 (텍스트에 없으면 'Unknown')
                2. job_title: 공고 제목 또는 직무명
                3. main_tasks: 주요 업무 (리스트)
                4. tech_stacks: 자격 요건이나 우대 사항에 있는 기술 스택 (리스트, 예: Python, AWS, React)
                5. start_date: 공고 시작일 (YYYY-MM-DD, 없으면 null)
                6. end_date: 공고 마감일 (YYYY-MM-DD, 상시채용은 null)
                7. ai_summary: 공고 전체 내용을 3줄 요약
                8. evaluation_criteria: 다음 4가지 기준에 맞추어 평가 기준 추출 (리스트)
                   - 직무 적합성 (Job Fit): 해당 직무를 수행하는 데 필요한 경험과 스킬
                   - 문화 적합성 (Culture Fit): 회사의 인재상, 비전, 핵심 가치와의 일치 여부
                   - 성장 가능성 (Growth Potential): 지속적인 학습 의지와 자기 주도적인 성장 태도
                   - 문제 해결 능력 (Problem Solving): 복잡한 문제를 분석하고 논리적으로 해결하는 역량
                   각 항목은 {{"name": "기준명", "description": "상세 설명"}} 형태여야 함.
                
                출력 포맷:
                {format_instructions}
                """,
                    ),
                    ("user", "{raw_text}"),
                ]
            )

            # 체인 연결
            chain = prompt | self.llm | self.parser

            # 실행
            result = await chain.ainvoke(
                {
                    "raw_text": raw_text[:15000],  # 토큰 제한 고려하여 절삭
                    "format_instructions": self.parser.get_format_instructions(),
                }
            )

            # PydanticOutputParser는 이미 Pydantic 객체를 반환하므로 바로 리턴
            return result

        except Exception as e:
            logger.error(f"❌ Extraction failed: {e}", exc_info=True)
            return None
