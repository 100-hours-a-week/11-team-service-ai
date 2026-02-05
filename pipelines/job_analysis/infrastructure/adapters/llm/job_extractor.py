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
                4. tech_stacks: 기술 스택 (리스트, 예: Python, AWS, React)
                5. start_date: 공고 시작일 (YYYY-MM-DD, 없으면 null)
                6. end_date: 공고 마감일 (YYYY-MM-DD, 상시채용은 null)
                7. ai_summary: 공고 전체 내용을 3줄 요약
                8. evaluation_criteria: 다음 4가지 기준에 맞추어 평가 기준 추출 (리스트)
                   - 직무 적합성
                   - 문화 적합성
                   - 성장 가능성
                   - 문제 해결 능력
                   각 항목은 {{"name": "기준명", "description": "상세 설명"}} 형태여야 함.
                
                반드시 아래와 같은 JSON 형식으로만 응답해주세요 (MarkDown Code Block 없이, 스키마 정의 없이, 순수 JSON 데이터만):
                {{
                    "company_name": "회사명",
                    "job_title": "직무명",
                    "main_tasks": ["업무1", "업무2"],
                    "tech_stacks": ["기술1", "기술2"],
                    "start_date": "2024-01-01",
                    "end_date": null,
                    "ai_summary": "요약 내용...",
                    "evaluation_criteria": [
                        {{"name": "직무 적합성", "description": "..."}},
                        {{"name": "문화 적합성", "description": "..."}}
                    ]
                }}
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
                    # "format_instructions": self.parser.get_format_instructions(), # Removed
                }
            )

            # PydanticOutputParser는 이미 Pydantic 객체를 반환하므로 바로 리턴
            logger.info(f"✅ Job extraction successful: {result.job_title} at {result.company_name}")
            return result

        except Exception as e:
            logger.error(f"❌ Extraction failed: {e}", exc_info=True)
            return None
