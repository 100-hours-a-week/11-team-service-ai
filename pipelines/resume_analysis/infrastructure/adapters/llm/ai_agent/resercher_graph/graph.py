import logging

from langgraph.graph import StateGraph, START, END
from langchain_core.runnables import RunnableConfig

from .state import ResearcherState, SubResearcherState
from ..configuration import AnalyseContext

from .node import (
    extract_unknown_tech_node,
    extract_tech_factor_node,
    research_stack_node,
    research_factor_node,
    vector_db_search_node,
    evaluate_threshold_router,
    ai_judge_node,
    ai_judge_router,
    tavily_search_node,
)

logger = logging.getLogger(__name__)


def build_common_search_subgraph():
    """개별 기술/키워드에 대한 공통 검색 파이프라인 (Sub-Graph) 구현"""
    builder = StateGraph(SubResearcherState)

    # 1. 노드 등록
    builder.add_node("vector_db_search_node", vector_db_search_node)
    builder.add_node("ai_judge_node", ai_judge_node)
    builder.add_node("tavily_search_node", tavily_search_node)

    # 2. 엣지 연결 (조건부 라우팅)
    builder.add_edge(START, "vector_db_search_node")

    builder.add_conditional_edges("vector_db_search_node", evaluate_threshold_router)
    builder.add_conditional_edges("ai_judge_node", ai_judge_router)

    builder.add_edge("tavily_search_node", END)

    return builder.compile()


# 서브그래프 인스턴스 (현재 Mock-up용, 나중에 research_tech_node 내부에서 호출 가능)
search_subgraph = build_common_search_subgraph()


class TechResearcher:
    """
    LangGraph 기반의 기술분석 에이전트 워크플로우
    """

    def __init__(self):
        self.graph = self._build_main_graph()

    def _build_main_graph(self):
        """메인 워크플로우 (Main-Graph) 구현"""
        builder = StateGraph(
            state_schema=ResearcherState, context_schema=AnalyseContext
        )

        # 1. 메인 노드 등록
        builder.add_node("extract_unknown_tech_node", extract_unknown_tech_node)
        builder.add_node("extract_tech_factor_node", extract_tech_factor_node)
        builder.add_node("research_stack_node", research_stack_node)
        builder.add_node("research_factor_node", research_factor_node)

        # 참고 (동적 라우팅 흐름):
        # 1. extract_unknown_tech_node -> research_stack_node (Send API 사용)
        # 2. extract_tech_factor_node -> research_factor_node (Send API 사용)
        # 3. 빈 리스트 방어를 위해 extract_* 노드에서 Command(goto=...)를 쓸 수도 있음

        # 2. 메인 플로우 엣지 설정
        builder.add_edge(START, "extract_unknown_tech_node")
        builder.add_edge("research_stack_node", "extract_tech_factor_node")
        builder.add_edge("research_factor_node", END)

        return builder.compile()

    async def start_researcher(
        self,
        config: RunnableConfig | dict,
        runtime: AnalyseContext,
    ) -> ResearcherState:
        """
        기술역량 분석 서브 파이프라인(LangGraph) 실행
        """
        # 초기 상태
        initial_state: ResearcherState = {
            "tech_info": [],
            "tech_competency_factors": [],
        }

        logger.info("기술 분석 서브 파이프라인 (TechResearcher) 실행 시작...")

        # 메인 그래프 완전 실행
        research_state = await self.graph.ainvoke(
            initial_state, config=config, context=runtime
        )

        logger.info("기술 분석 서브 파이프라인 (TechResearcher) 실행 완료!")
        return research_state
