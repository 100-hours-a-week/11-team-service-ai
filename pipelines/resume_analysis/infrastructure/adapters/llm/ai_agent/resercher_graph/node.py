import logging
from typing import Literal

from langchain_core.runnables import RunnableConfig
from langgraph.types import Send, Command
from langgraph.runtime import Runtime

from .state import ResearcherState, SubResearcherState, TechInfo, TechCompetencyFactor
from ..configuration import AnalyseContext

logger = logging.getLogger(__name__)

# AI가 이력서, 포트폴리오, 서류에서 모르는 기술 스택을 추출하는 노드
async def extract_unknown_tech_node(
    state: ResearcherState, config: RunnableConfig, runtime: Runtime[AnalyseContext]
):
    # TODO LLM호출하여 모르는 기술스택 추출해야 함
    unknown_tech = ["Redis", "Zustand"]

    sends = [
        Send("research_stack_node", {"keyword": tech, "result": ""})
        for tech in unknown_tech
    ]
    
    # [방어 로직] 모르는 기술이 1개도 없다면 워커가 생기지 않으므로 직접 다음 노드로 점프
    if not sends:
        return Command(goto="extract_tech_factor_node")
        
    return Command(goto=sends)

# 기술역량 키워드 추출노드
async def extract_tech_factor_node(
    state: ResearcherState, config: RunnableConfig, runtime: Runtime[AnalyseContext]
):
    # TODO unknown_tech를 컨텍스트에 추가하고 평가 키워드를 추출해야 함
    tech_factors = ["Redis를 활용한 대규모 오버헤드 처리", "Zustand 도입을 통한 리렌더링 최적화"]

    sends = [
        Send("research_factor_node", {"keyword": factor, "result": ""})
        for factor in tech_factors
    ]
    
    # [방어 로직] 평가 키워드가 도출되지 않았다면 전체 서브그래프 즉시 종료
    if not sends:
        return Command(goto="__end__")
        
    return Command(goto=sends)

# TODO 3-1. 메인 - 서브그래프 어댑터 래퍼 노드 (기술 스택 검색용)
async def research_stack_node(
    state: SubResearcherState, config: RunnableConfig, runtime: Runtime[AnalyseContext]
):
    keyword = state.get("keyword")
    
    # 실제 공통 서브그래프(search_subgraph.ainvoke) 호출!
    from .graph import search_subgraph
    result_state = await search_subgraph.ainvoke(state, config=config, context=runtime)
    result = result_state.get("result", "검색실패")

    info = TechInfo(subject=keyword, content=result)
    return {"tech_info": [info]}

# TODO 3-2. 메인 - 서브그래프 어댑터 래퍼 노드 (평가 키워드 검색용)
async def research_factor_node(
    state: SubResearcherState, config: RunnableConfig, runtime: Runtime[AnalyseContext]
):
    keyword = state.get("keyword")
    
    # 실제 공통 서브그래프(search_subgraph.ainvoke) 호출!
    from .graph import search_subgraph
    result_state = await search_subgraph.ainvoke(state, config=config, context=runtime)
    result = result_state.get("result", "검색실패")

    factor = TechCompetencyFactor(factor_name=keyword, content=result)
    return {"tech_competency_factors": [factor]}


# ======================================================================
# [공통 서브그래프용 노드들 (State: SubResearcherState 내에서 순환)]
# ======================================================================

# TODO 공통 1. 벡터DB 검색 노드
async def vector_db_search_node(
    state: SubResearcherState, config: RunnableConfig, runtime: Runtime[AnalyseContext]
):
    keyword = state["keyword"]
    logger.info(f"[{keyword}] 벡터 DB 검색 중...")
    # TODO 벡터db검색 필요
    # 목업 결과: 실제로는 Weaviate 등에서 score를 반환해야 합니다.
    # 테스트를 위해 임의의 점수를 부여 (0.0 ~ 1.0)
    mock_score = 0.85 if "Redis" in keyword else (0.3 if "대규모" in keyword else 0.6)
    
    return {
        "result": f"[DB검색 기반] {keyword} 기본 지식 데이터",
        "search_score": mock_score
    }

# TODO 공통 2. 임계점 판별 라우터 (AI를 통해 적절한 데이터인지 확인 전 1차 필터링)
def evaluate_threshold_router(
    state: SubResearcherState
) -> Literal["__end__", "ai_judge_node", "tavily_search_node"]:
    keyword = state["keyword"]
    score = state.get("search_score", 0.0)
    logger.info(f"[{keyword}] 임계점 판별 라우팅 중... (Score: {score})")
    
    # score 기반 분기 (실제 운영 시에는 이 값을 config 등으로 조절 가능)
    if score >= 0.8:
        # 임계점 높음 -> 종료 (충분한 정보이므로 바로 서브그래프 탈출)
        return "__end__"
    elif score <= 0.4:
        # 임계점 낮음 -> 정보가 너무 없어 바로 외부 검색
        return "tavily_search_node"
    else:
        # 임계점 애매 (0.4 ~ 0.8) -> AI 판별로 넘겨서 적합한지 검증
        return "ai_judge_node"

# TODO 공통 3. AI 판별 노드 (임계점 애매한 경우 데이터 적합성 평가)
async def ai_judge_node(
    state: SubResearcherState, config: RunnableConfig, runtime: Runtime[AnalyseContext]
):
    keyword = state["keyword"]
    logger.info(f"[{keyword}] AI 판별 노드에서 데이터 적합성 평가 중...")
    # TODO AI를 통한 유사도 평가 필요
    current_result = state.get("result", "")
    
    # Mock-up: "Zustand"가 포함되어 있으면 부적합(False)으로 판별한다고 가정
    mock_is_valid = False if "Zustand" in keyword else True
    
    return {
        "result": current_result + " -> [AI 검증 시도됨]",
        "is_valid": mock_is_valid
    }

# TODO 공통 4. AI 판별 결과에 따른 라우터
def ai_judge_router(state: SubResearcherState) -> Literal["__end__", "tavily_search_node"]:
    is_valid = state.get("is_valid", False)
    
    # AI 평가 결과에 따라 명확하게 분기
    if is_valid:
        return "__end__" # 유사함 (정보 충분) -> 종료
    else:
        return "tavily_search_node" # 유사하지 않음 (정보 부족) -> 웹 검색 보강

# TODO 공통 5. tavily 검색 + 청킹 + 임베딩 노드
async def tavily_search_node(
    state: SubResearcherState, config: RunnableConfig, runtime: Runtime[AnalyseContext]
):
    keyword = state["keyword"]
    logger.info(f"[{keyword}] Tavily 웹 검색 및 임베딩 진행 중...")
    
    current_result = state.get("result", "")
    return {"result": current_result + " -> [Tavily 웹 검색 보강된 지식]"}