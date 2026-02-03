
import logging
from typing import List
from ....domain.interface.adapter_interfaces import AnalystAgent
from ....domain.models.job import JobInfo, EvaluationCriteria
from ....domain.models.evaluation import CompetencyResult
from ....domain.models.report import OverallFeedback

logger = logging.getLogger(__name__)

class MockAnalyst(AnalystAgent):
    """
    개발 및 테스트용 Mock Agent
    실제 LLM 호출 없이 고정된 더미 데이터를 반환합니다.
    """

    async def evaluate_competency(
        self,
        job_info: JobInfo,
        criteria: EvaluationCriteria,
        resume_text: str,
        portfolio_text: str,
    ) -> CompetencyResult:
        logger.info(f"[Mock] evaluate_competency called for: {criteria.name}")
        return CompetencyResult(
            name=criteria.name,
            score=75.0,
            description=f"[Mock] {criteria.name}에 대한 긍정적인 평가 결과입니다.",
        )

    async def synthesize_report(
        self, job_info: JobInfo, competency_results: List[CompetencyResult]
    ) -> OverallFeedback:
        logger.info("[Mock] synthesize_report called")
        return OverallFeedback(
            one_line_review="[Mock] 기술적 역량이 우수하며 성장 가능성이 높은 지원자입니다.",
            feedback_detail="[Mock] 강점: 관련 기술 경험이 풍부합니다. 보완점: 대규모 시스템 경험을 쌓으면 좋겠습니다.",
        )
