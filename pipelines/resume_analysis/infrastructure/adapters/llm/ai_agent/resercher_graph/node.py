import logging
from typing import Literal

from langchain_core.runnables import RunnableConfig
from langgraph.types import Send, Command
from langgraph.runtime import Runtime

from pydantic import BaseModel, Field

from .state import ResearcherState, SubResearcherState, TechInfo, TechCompetencyFactor
from ..configuration import AnalyseContext, Configuration
from .prompt import EXTRACT_UNKNOWN_TECH_PROMPT, EXTRACT_TECH_FACTOR_PROMPT
from shared.utils import load_chat_model

logger = logging.getLogger(__name__)

# AI가 이력서, 포트폴리오, 서류에서 모르는 기술 스택을 추출하는 노드
async def extract_unknown_tech_node(
    state: ResearcherState, config: RunnableConfig, runtime: Runtime[AnalyseContext]
):
    class UnknownTechList(BaseModel):
        techs: list[str] = Field(description="추출된 모르는 기술 스택 또는 키워드 목록")

    cfg = Configuration.from_runnable_config(config)
    rtx = runtime.context

    llm = load_chat_model(cfg.model_name, cfg.model_provider)
    prompt = EXTRACT_UNKNOWN_TECH_PROMPT
    chain = prompt | llm.with_structured_output(UnknownTechList)

    result = await chain.ainvoke(
        {
            "job_info": rtx.job_info.model_dump_json(ensure_ascii=False) if hasattr(rtx.job_info, "model_dump_json") else str(rtx.job_info),
            "doc_text": rtx.doc_text
        }
    )

    unknown_tech = result.techs if result and result.techs else []
    
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
    class TechFactorsList(BaseModel):
        tech_factors: list[str] = Field(description="추출된 모르는 기술 스택 또는 키워드 목록")

    cfg = Configuration.from_runnable_config(config)
    rtx = runtime.context

    llm = load_chat_model(cfg.model_name, cfg.model_provider)
    prompt = EXTRACT_TECH_FACTOR_PROMPT
    chain = prompt | llm.with_structured_output(TechFactorsList)

    result = await chain.ainvoke(
        {
            "job_info": rtx.job_info.model_dump_json(ensure_ascii=False) if hasattr(rtx.job_info, "model_dump_json") else str(rtx.job_info),
            "doc_text": rtx.doc_text,
            "tech_info": [info.model_dump() for info in state.get("tech_info", [])]
        }
    )

    tech_factors = result.tech_factors if result and result.tech_factors else []

    sends = [
        Send("research_factor_node", {"keyword": factor, "result": ""})
        for factor in tech_factors
    ]
    
    # [방어 로직] 평가 키워드가 도출되지 않았다면 전체 서브그래프 즉시 종료
    if not sends:
        return Command(goto="__end__")
        
    return Command(goto=sends)

# 메인 - 서브그래프 어댑터 래퍼 노드 (기술 스택 검색용)
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

# 메인 - 서브그래프 어댑터 래퍼 노드 (평가 키워드 검색용)
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

# 벡터DB 검색 노드
async def vector_db_search_node(
    state: SubResearcherState, config: RunnableConfig, runtime: Runtime[AnalyseContext]
):
    keyword = state["keyword"]
    logger.info(f"[{keyword}] 벡터 DB 검색 중...")
    # TODO 벡터db검색 필요
    # 목업 결과: 실제로는 Weaviate 등에서 score를 반환해야 합니다.
    # 테스트를 위해 임의의 점수를 부여 (0.0 ~ 1.0)
    mock_score = 0.5
    
    return {
        "result": f"[DB검색 기반] {keyword} 기본 지식 데이터",
        "search_score": mock_score
    }

# 임계점 판별 라우터 (AI를 통해 적절한 데이터인지 확인 전 1차 필터링)
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

# AI 판별 노드 (임계점 애매한 경우 데이터 적합성 평가)
async def ai_judge_node(
    state: SubResearcherState, config: RunnableConfig, runtime: Runtime[AnalyseContext]
):
    keyword = state["keyword"]
    logger.info(f"[{keyword}] AI 판별 노드에서 데이터 적합성 평가 중...")
    # TODO AI를 통한 유사도 평가 필요
    current_result = state.get("result", "")
    
    # Mock-up: "Zustand"가 포함되어 있으면 부적합(False)으로 판별한다고 가정
    mock_is_valid = False
    
    return {
        "result": current_result + " -> [AI 검증 시도됨]",
        "is_valid": mock_is_valid
    }

# AI 판별 결과에 따른 라우터
def ai_judge_router(state: SubResearcherState) -> Literal["__end__", "tavily_search_node"]:
    is_valid = state.get("is_valid", False)
    
    # AI 평가 결과에 따라 명확하게 분기
    if is_valid:
        return "__end__" # 유사함 (정보 충분) -> 종료
    else:
        return "tavily_search_node" # 유사하지 않음 (정보 부족) -> 웹 검색 보강

from tavily import AsyncTavilyClient
from shared.config import settings

# tavily 검색 (현재는 문서 추가 없이 컨텍스트 텍스트만 덧붙임)
# TODO 청킹 + 임베딩 로직 추가 필요
async def tavily_search_node(
    state: SubResearcherState, config: RunnableConfig, runtime: Runtime[AnalyseContext]
):
    keyword = state["keyword"]
    logger.info(f"[{keyword}] Tavily 웹 검색 진행 중...")
    
    current_result = state.get("result", "")

    try:
        # 1. 비동기 클라이언트로 Tavily API 호출
        client = AsyncTavilyClient(api_key=settings.TAVILY_API_KEY)
        
        # 2. 쿼리 생성 및 탐색
        query = f"{keyword} 기술의 핵심 개념과 동작 원리, 활용 사례"
        response = await client.search(
            query=query,
            search_depth="advanced",
            include_answer=True, # Tavily가 자체적으로 요약한 텍스트 활성화
            max_results=3        # 너무 긴 컨텍스트 방지를 위해 결과 개수 제한
        )
        
        # 3. 검색 결과 컨텍스트 구성
        # 1순위: Tavily의 AI가 요약한 파편화되지 않은 직관적인 답변
        if response.get("answer"):
            tavily_context = response["answer"]
        # 2순위: 답변이 생성되지 않았다면, 검색된 개별 결과물의 본문을 연결
        else:
            results = response.get("results", [])
            tavily_context = "\n\n".join([f"- {r.get('title', '웹문서')}: {r.get('content', '')}" for r in results])
            
        if not tavily_context:
            tavily_context = "추가적인 웹 검색 결과가 없습니다."

    except Exception as e:
        logger.error(f"[{keyword}] Tavily 검색 중 에러 발생: {e}")
        tavily_context = f"웹 검색 실패 ({str(e)})"
    
    # 4. 기존 (VDB 등에서 가져왔던) 결과에 웹 검색 문서를 보강하여 반환
    final_result = f"{current_result}\n\n[Tavily 웹 검색 보강 자료]\n{tavily_context}".strip()
    
    return {"result": final_result}