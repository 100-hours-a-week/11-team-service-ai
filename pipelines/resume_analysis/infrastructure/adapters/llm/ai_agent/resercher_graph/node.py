import logging
from typing import Literal

from langchain_core.runnables import RunnableConfig
from langgraph.types import Send, Command
from langgraph.runtime import Runtime

from pydantic import BaseModel, Field

from tavily import AsyncTavilyClient
from shared.config import settings
from .retrieval import make_weaviate_store

from .state import ResearcherState, SubResearcherState, TechInfo, TechCompetencyFactor
from ..configuration import AnalyseContext, Configuration
from .prompt import (
    EXTRACT_UNKNOWN_TECH_PROMPT,
    EXTRACT_TECH_FACTOR_PROMPT,
    EVALUATE_CONTEXT_PROMPT,
)
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
            "job_info": (
                rtx.job_info.model_dump_json(
                    include={"company_name", "main_tasks", "tech_stacks", "summary"},
                    ensure_ascii=False,
                )
                if hasattr(rtx.job_info, "model_dump_json")
                else str(rtx.job_info)
            ),
            "doc_text": rtx.doc_text,
        }
    )

    unknown_tech = getattr(result, "techs", []) if result else []
    logger.info(f"[추출된 모르는 기술 스택] {unknown_tech}")

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
        tech_factors: list[str] = Field(
            description="가장 핵심적인 3가지 리서치 및 기술 평가 키워드 (영어)"
        )

    cfg = Configuration.from_runnable_config(config)
    rtx = runtime.context

    llm = load_chat_model(cfg.model_name, cfg.model_provider)
    prompt = EXTRACT_TECH_FACTOR_PROMPT
    chain = prompt | llm.with_structured_output(TechFactorsList)

    result = await chain.ainvoke(
        {
            "job_info": (
                rtx.job_info.model_dump_json(
                    include={"company_name", "main_tasks", "tech_stacks", "summary"},
                    ensure_ascii=False,
                )
                if hasattr(rtx.job_info, "model_dump_json")
                else str(rtx.job_info)
            ),
            "doc_text": rtx.doc_text,
            "tech_info": [info.model_dump() for info in state.get("tech_info", [])],
        }
    )

    tech_factors = getattr(result, "tech_factors", []) if result else []
    logger.info(f"[추출된 기술 역량 키워드] {tech_factors}")

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
# ======================================================================


# 벡터DB 검색 노드
from infinity_client import Client
from langchain_classic.retrievers.contextual_compression import ContextualCompressionRetriever
from langchain_community.document_compressors.infinity_rerank import InfinityRerank

async def vector_db_search_node(
    state: SubResearcherState, config: RunnableConfig, runtime: Runtime[AnalyseContext]
):
    keyword = state["keyword"]
    logger.info(f"[{keyword}] 벡터 DB 검색 중...")

    # 1. DB에서 검색 수행
    with make_weaviate_store() as store:
        # 비동기 상황이므로 ainvoke를 사용하여 문서 검색
        retriever = store.as_retriever(search_kwargs={"k": 5})

        client = Client(base_url=settings.RERANKER_MODEL_URL)

        compressor = InfinityRerank(client=client, model=settings.RERANKER_MODEL)
        
        compression_retriever = ContextualCompressionRetriever(
            base_compressor=compressor, base_retriever=retriever
        )

        compressed_docs = await compression_retriever.ainvoke(keyword)

    # 2. 검색 결과가 아예 없는 경우
    if not compressed_docs:
        logger.info(f"[{keyword}] 벡터 DB 검색 결과 없음.")
        return {
            "result": "",
            "search_score": 0.0,  # 외부 검색(Tavily)로 바로 빠지게 점수를 낮춤
        }

    # 3. 검색된 문서 내용 병합
    top_doc = compressed_docs[0]
    top_score = top_doc.metadata.get("relevance_score", 0.0)

    logger.info(f"[{keyword}] 검색 성공! (점수: {top_score})")

    return {"result": top_doc.page_content, "search_score": float(top_score)}


# 임계점 판별 라우터 (AI를 통해 적절한 데이터인지 확인 전 1차 필터링)
def evaluate_threshold_router(
    state: SubResearcherState,
) -> Literal["__end__", "ai_judge_node", "tavily_search_node"]:

    score = state.get("search_score", 0.0)

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
    class ValidContextEval(BaseModel):
        is_valid: bool = Field(
            description="제공된 컨텍스트가 검색 대상을 이해하기에 유효한지 여부 (유효하면 True, 쓸모없으면 False)"
        )

    keyword = state["keyword"]

    current_result = state.get("result", "")
    cfg = Configuration.from_runnable_config(config)
    llm = load_chat_model(cfg.model_name, cfg.model_provider)

    chain = EVALUATE_CONTEXT_PROMPT | llm.with_structured_output(ValidContextEval)

    # AI에게 키워드와, 앞서 DB에서 검색해온 내용을 넘겨 실제로 쓸모있는지 판별시킴
    eval_result = await chain.ainvoke({"keyword": keyword, "context": current_result})

    # 판별 결과(True/False) 추출
    is_valid = getattr(eval_result, "is_valid", False) if eval_result else False

    return {"result": current_result, "is_valid": is_valid}


# AI 판별 결과에 따른 라우터
def ai_judge_router(
    state: SubResearcherState,
) -> Literal["__end__", "tavily_search_node"]:
    is_valid = state.get("is_valid", False)

    # AI 평가 결과에 따라 명확하게 분기
    if is_valid:
        return "__end__"  # 유사함 (정보 충분) -> 종료
    else:
        return "tavily_search_node"  # 유사하지 않음 (정보 부족) -> 웹 검색 보강


# tavily 검색 -> 청킹 -> 임베딩
async def tavily_search_node(
    state: SubResearcherState, config: RunnableConfig, runtime: Runtime[AnalyseContext]
):
    keyword = state["keyword"]
    logger.info(f"[{keyword}] Tavily 웹 검색 진행 중...")

    try:
        # 1. 비동기 클라이언트로 Tavily API 호출
        client = AsyncTavilyClient(api_key=settings.TAVILY_API_KEY)

        try:
            # 2. 쿼리 생성 및 탐색
            response = await client.search(
                query=keyword,
                search_depth="advanced",
                include_answer=True,  # Tavily가 자체적으로 요약한 텍스트 활성화
                max_results=3,  # 너무 긴 컨텍스트 방지를 위해 결과 개수 제한
            )

            # 3. [ingest.py 활용] 검색된 문서를 벡터 DB에 실시간으로 청킹/임베딩 (비동기 처리)
            # ingest.py의 ingest_docs 함수는 문서 청킹, 임베딩은 cpu작업이기 때문에 비동기 처리를 위해 서브 쓰레드에서 실행
            try:
                import asyncio
                from .ingest import ingest_docs

                # response 객체를 그대로 넘겨주어 ingest.py의 내부 로직(Document 생성, RecursiveCharacterTextSplitter, SQLRecordManager, index 저장)
                await asyncio.to_thread(ingest_docs, response)
                logger.info(f"[{keyword}] Tavily 검색 결과 DB 인덱싱 완료")
            except Exception as ingest_error:
                logger.error(
                    f"[{keyword}] 인덱싱 중 에러 발생 (검색 컨텍스트는 계속 유지): {ingest_error}"
                )

            # 4. 검색 결과 컨텍스트 구성
            # 답변이 생성되지 않았다면, 검색된 결과 중 score가 가장 높은 1개만 선별
            results = response.get("results", [])
            if results:
                best_result = max(results, key=lambda x: x.get("score", 0))
                tavily_context = f"- {best_result.get('title', '웹문서')}: {best_result.get('content', '')}"
            else:
                tavily_context = ""

        finally:
            # ✨ 정석적인 클라이언트 통신 소켓 종료 (ResourceWarning 영구 방지)
            await client.close()

    except Exception as e:
        logger.error(f"[{keyword}] Tavily 검색 중 에러 발생: {e}")

    return {"result": tavily_context}
