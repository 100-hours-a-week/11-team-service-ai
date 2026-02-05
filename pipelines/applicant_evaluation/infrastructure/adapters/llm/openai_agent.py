import logging
from typing import List

from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from ....domain.interface.adapter_interfaces import AnalystAgent
from ....domain.models.job import JobInfo, EvaluationCriteria
from ....domain.models.evaluation import CompetencyResult
from ....domain.models.report import OverallFeedback

logger = logging.getLogger(__name__)


class LLMAnalyst(AnalystAgent):
    """
    LLM(LangChain)을 사용하여 지원자를 분석하는 AI 에이전트.
    특정 LLM 구현체에 의존하지 않고 BaseChatModel을 주입받아 사용합니다.
    """

    def __init__(self, llm: BaseChatModel):
        self.llm = llm

    async def evaluate_competency(
        self,
        job_info: JobInfo,
        criteria: EvaluationCriteria,
        resume_text: str,
        portfolio_text: str,
    ) -> CompetencyResult:
        """
        단일 평가 기준에 대해 점수와 이유를 생성
        """
        parser = PydanticOutputParser(pydantic_object=CompetencyResult)

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """
            당신은 전문적인 채용 담당관입니다. 
            지원자가 '{company_name}' 회사의 다음 직무에 지원했습니다.
            
            [직무 정보]
            - 주요 업무: {main_tasks}
            - 기술 스택: {tech_stacks}
            
            당신의 임무는 지원자의 서류(이력서, 포트폴리오)를 분석하여 
            다음 평가 기준: '{criteria_name}' ({criteria_desc})
            에 대해 0~100점 사이의 점수를 매기고 구체적인 근거를 서술하는 것입니다.

            반드시 아래와 같은 JSON 형식으로만 응답해주세요 (MarkDown Code Block 없이, 스키마 정의 없이, 순수 JSON 데이터만):
            {{
                "name": "{criteria_name}",
                "score": 85.0, 
                "description": "평가 근거 및 상세 사유..."
            }}
            """,
                ),
                (
                    "user",
                    """
            [이력서 내용]
            {resume_text}

            [포트폴리오 내용]
            {portfolio_text}
            """,
                ),
            ]
        )

        chain = prompt | self.llm | parser

        try:
            result = await chain.ainvoke(
                {
                    "company_name": job_info.company_name,
                    "main_tasks": ", ".join(job_info.main_tasks),
                    "tech_stacks": ", ".join(job_info.tech_stacks),
                    "criteria_name": criteria.name,
                    "criteria_desc": criteria.description,
                    "resume_text": resume_text[:10000],
                    "portfolio_text": portfolio_text[:10000],
                    # "format_instructions": parser.get_format_instructions(), # Removed
                }
            )

            logger.info(
                f"✅ Evaluated criteria: {criteria.name} (Score: {result.score})"
            )

            return CompetencyResult(
                name=criteria.name, score=result.score, description=result.description
            )
            
        except Exception as e:
            logger.error(f"❌ Evaluation failed for {criteria.name}: {e}")
            # 실패 시 기본값 반환 혹은 재시도 로직 (여기선 0점 처리)
            return CompetencyResult(
                name=criteria.name, score=0.0, description=f"Evaluation Error: {str(e)}"
            )

    async def synthesize_report(
        self, job_info: JobInfo, competency_results: List[CompetencyResult]
    ) -> OverallFeedback:
        """
        개별 평가 결과를 종합하여 최종 리포트 생성
        """
        parser = PydanticOutputParser(pydantic_object=OverallFeedback)

        # 평가 결과 요약 텍스트 생성
        results_summary = "\n".join(
            [f"- {r.name}: {r.score}점. {r.description}" for r in competency_results]
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """
            당신은 채용 결정권자입니다. 
            '{company_name}' 회사의 채용 공고에 대한 지원자 평가 결과가 다음과 같이 취합되었습니다.

            [직무 요약]
            {job_summary}

            [평가 결과 요약]
            {results_summary}

            위 정보를 바탕으로 채용 담당자 관점에서 다음 두 가지를 작성해주세요.
            1. 한 줄 평가 (one_line_review): 지원자의 핵심 역량과 회사 적합도를 한 문장으로 요약
            2. 상세 피드백 (feedback_detail): 직무 기술서(JD)와 지원자 역량을 비교하여, 강점과 보완점을 구체적으로 서술
            
            반드시 아래와 같은 JSON 형식으로만 응답해주세요 (MarkDown Code Block 없이, 스키마 정의 없이, 순수 JSON 데이터만):
            {{
                "one_line_review": "지원자의 한 줄 평가...",
                "feedback_detail": "상세 피드백 내용..."
            }}
            """,
                ),
                ("user", "종합적인 채용 리포트를 작성해주세요."),
            ]
        )

        chain = prompt | self.llm | parser

        try:
            result = await chain.ainvoke(
                {
                    "company_name": job_info.company_name,
                    "job_summary": job_info.summary[:500],
                    "results_summary": results_summary,
                    # "format_instructions": parser.get_format_instructions(), # Removed
                }
            )

            return OverallFeedback(
                one_line_review=result.one_line_review,
                feedback_detail=result.feedback_detail,
            )

        except Exception as e:
            logger.error(f"❌ Report synthesis failed: {e}")
            return OverallFeedback(
                one_line_review="Error generating report.",
                feedback_detail=f"An error occurred: {str(e)}",
            )
