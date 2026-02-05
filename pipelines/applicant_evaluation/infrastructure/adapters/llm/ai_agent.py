import logging
from typing import List

from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import PydanticOutputParser

from ....domain.interface.adapter_interfaces import AnalystAgent
from ....domain.models.job import JobInfo, EvaluationCriteria
from ....domain.models.evaluation import CompetencyResult
from ....domain.models.report import OverallFeedback
from .prompts import get_competency_evaluation_prompt, get_report_synthesis_prompt

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

        prompt = get_competency_evaluation_prompt()

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

        prompt = get_report_synthesis_prompt()

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
