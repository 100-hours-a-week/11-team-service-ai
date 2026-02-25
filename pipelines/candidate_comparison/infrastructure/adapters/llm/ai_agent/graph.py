import logging
from typing import Tuple, cast
from langchain_core.runnables import RunnableConfig

from langgraph.graph import StateGraph, START, END

from .....domain.interface.adapter_interfaces import ComparisonAnalyzer
from .....domain.models.job import JobInfo
from .....domain.models.candidate import Candidate

# Import local modules (relative)
from .configuration import CandidateContext
from .state import CandidateState
from .nodes import (
    agent_me_attack,
    agent_competitor_attack,
    finalize_evaluation,
    check_turn,
)

logger = logging.getLogger(__name__)


class LLMAnalyst(ComparisonAnalyzer):
    """
    LangGraph 기반의 AI 분석 에이전트 (Map-Reduce Orchestrator)
    """

    def __init__(self, model_name: str = "gpt-4o", model_provider: str = "openai"):
        self.model_name = model_name
        self.model_provider = model_provider

    async def analyze_candidates(
        self,
        my_candidate: Candidate,
        competitor_candidate: Candidate,
        job_info: JobInfo,
    ) -> Tuple[str, str]:
        """
        문서 분석 전체 파이프라인(LangGraph) 실행
        """

        builder = StateGraph(
            state_schema=CandidateState, context_schema=CandidateContext
        )
        builder.add_node("agent_me_attack", agent_me_attack)  # type: ignore
        builder.add_node("agent_competitor_attack", agent_competitor_attack)  # type: ignore
        builder.add_node("finalize_evaluation", finalize_evaluation)  # type: ignore

        builder.add_edge(START, "agent_me_attack")
        builder.add_edge("agent_me_attack", "agent_competitor_attack")

        builder.add_conditional_edges(
            source="agent_competitor_attack",  # 조건부 로직을 시작할 노드
            path=check_turn,  # 조건을 판단할 함수
            path_map={
                "continue": "agent_me_attack",  # 함수의 반환값이 "continue"면 agent_me_attack로 이동
                "end": "finalize_evaluation",  # 함수의 반환값이 "end"면 finalize_evaluation로 이동
            },
        )

        builder.add_edge("finalize_evaluation", END)

        graph = builder.compile()

        # 실행 설정 (모델 변경 등)
        config = cast(
            RunnableConfig,
            {
                "configurable": {
                    "model_provider": self.model_provider,
                    "model_name": self.model_name,
                }
            },
        )

        context_data = CandidateContext(
            job_info=job_info,
            my_candidate=my_candidate,
            competitor_candidate=competitor_candidate,
        )

        # 그래프 실행
        final_state = await graph.ainvoke(
            input=CandidateState(turn_count=0, messages=[]),  # type: ignore
            config=config,
            context=context_data,
        )

        return (final_state["strengths"], final_state["weaknesses"])
