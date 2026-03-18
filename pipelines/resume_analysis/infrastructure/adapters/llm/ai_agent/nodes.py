from langchain_core.language_models.chat_models import BaseChatModel
import logging
from typing import List, Union

from langchain_core.runnables import RunnableConfig

from .....domain.models.document import DocumentType
from .....domain.models.report import SectionAnalysis
from .....domain.models.report import ResumeAnalysisType, PortfolioAnalysisType
from .state import AnalysisState
from langgraph.runtime import Runtime
from langgraph.types import Send, Command


from .configuration import AnalyseContext, Configuration
from .prompts import (
    get_analysis_prompt,
    get_final_report_prompt,
    PORTFOLIO_TECHNICAL_DEPTH_PROMPT,
)
from shared.utils import load_chat_model, AiResponse
from .resercher_graph.graph import TechResearcher
from .resercher_graph.state import ResearcherState

logger = logging.getLogger(__name__)


def plan_analysis(state: AnalysisState, runtime: Runtime[AnalyseContext]):
    target_doc_type = runtime.context.doc_type

    logger.info(f"PLAN: Analyzing {target_doc_type}")

    # execute_analysis_node에 analyse_type을 전달하여 병렬적으로 실행
    # Send로 실행되는 node의 State는 전체 그래프의 State와 분리됨
    if target_doc_type == DocumentType.RESUME:
        sends = [
            Send("execute_resume_analysis_node", {"analyse_type": type.value})
            for type in ResumeAnalysisType
        ]
        return Command(goto=sends)
    elif target_doc_type == DocumentType.PORTFOLIO:
        # 기술문서 추출 노드로 이동 (Fan-out 전 전처리)
        return Command(goto="extracted_tech_document")

async def extracted_tech_document(state: AnalysisState, config: RunnableConfig, runtime: Runtime[AnalyseContext]):
    rtx = runtime.context
    try:
        # 1. 서브 그래프를 생성하여 tech_info 정보를 가져옴
        researcher = TechResearcher()
        research_state = await researcher.start_researcher(config=config, runtime=rtx)

        # 2. 다음 단계(Fan-out)를 위한 Send 리스트 생성
        # 추출된 research_state를 각 노드에 전달함
        sends = [
            Send("execute_portfolio_analysis_node", {
                "analyse_type": type.value, 
                "researcher_state": research_state
            })
            for type in PortfolioAnalysisType
        ]

        return Command(goto=sends)

    except Exception as e:
        logger.error(f"Extraction Failed: {e}")
        # 실패 시 research_state 없이 진행
        sends = [
            Send("execute_portfolio_analysis_node", {"analyse_type": type.value})
            for type in PortfolioAnalysisType
        ]
        return Command(goto=sends)


async def execute_portfolio_analysis_node(
    input_state: dict[str, Union[str, ResearcherState]],
    config: RunnableConfig,
    runtime: Runtime[AnalyseContext],
):
    """포트폴리오 각 항목에 대한 분석을 수행하는 노드 (Parallel Worker)"""
    analysis_type = input_state.get("analyse_type")
    research_state = input_state.get("researcher_state")
    
    cfg = Configuration.from_runnable_config(config)
    rtx = runtime.context
    llm = load_chat_model(cfg.model_name, cfg.model_provider)

    logger.info(f"[{cfg.model_name}] Analyzing Portfolio Section: {analysis_type} ...")

    try:
        # 포트폴리오 전용 분석 헬퍼 호출
        result = await _analyze_portfolio_section(rtx, str(analysis_type), llm, research_state)
        return {"section_analyses": [result]}
    except Exception as e:
        logger.error(f"Portfolio Analysis Failed for {analysis_type}: {e}")
        return {"section_analyses": []}


async def execute_resume_analysis_node(
    input_state: dict[str, str],
    config: RunnableConfig,
    runtime: Runtime[AnalyseContext],
):
    """이력서 각 항목에 대한 분석을 수행하는 노드 (Parallel Worker)"""
    analysis_type = input_state.get("analyse_type")
    
    cfg = Configuration.from_runnable_config(config)
    rtx = runtime.context
    llm = load_chat_model(cfg.model_name, cfg.model_provider)

    logger.info(f"[{cfg.model_name}] Analyzing Resume Section: {analysis_type} ...")

    try:
        # 이력서 전용 분석 헬퍼 호출
        result = await _analyze_resume_section(rtx, str(analysis_type), llm)
        return {"section_analyses": [result]}
    except Exception as e:
        logger.error(f"Resume Analysis Failed for {analysis_type}: {e}")
        return {"section_analyses": []}


async def _analyze_portfolio_section(
    rtx: AnalyseContext,
    analysis_type: str,
    llm: BaseChatModel,
    research_state: ResearcherState = None,
) -> SectionAnalysis:
    """포트폴리오 분석 로직 (기술 문맥 통합)"""
    typed_type = PortfolioAnalysisType(analysis_type)
    
    # 1. 기술 문맥 문자열 생성
    tech_contexts_str = "분석 정보 없음"
    factors_str = "분석 정보 없음"
    if research_state:
        tech_info = research_state.get("tech_info", [])
        factors = research_state.get("tech_competency_factors", [])
        if tech_info:
            tech_contexts_str = "\n".join([f"- [{i.subject}]: {i.content}" for i in tech_info])
        if factors:
            factors_str = "\n".join([f"- {f.factor_name}: {f.content}" for f in factors])

    # 2. 프롬프트 선택 (Technical Depth는 전용 프롬프트 유지)
    if typed_type == PortfolioAnalysisType.TECHNICAL_DEPTH:
        prompt = PORTFOLIO_TECHNICAL_DEPTH_PROMPT
    else:
        prompt = get_analysis_prompt(analysis_type)

    chain = prompt | llm.with_structured_output(AiResponse, method="json_mode")
    job_info = rtx.job_info
    job_title = job_info.summary.splitlines()[0] if job_info.summary else job_info.company_name

    # 3. LLM 호출
    result = await chain.ainvoke({
        "job_title": job_title,
        "summary": job_info.summary or "내용 없음",
        "tech_stacks": ", ".join(job_info.tech_stacks) if job_info.tech_stacks else "정보 없음",
        "main_tasks": ", ".join(job_info.main_tasks) if job_info.main_tasks else "정보 없음",
        "qualifications": ", ".join(getattr(job_info, "qualifications", [])) or "정보 없음",
        "preferred_points": ", ".join(getattr(job_info, "preferred_points", [])) or "정보 없음",
        "doc_text": rtx.doc_text,
        "analysis_type": analysis_type,
        "tech_contexts": tech_contexts_str,
        "evaluation_factors": factors_str,
    })

    if not isinstance(result, AiResponse):
        raise TypeError(f"Expected AiResponse but got {type(result)}")

    return SectionAnalysis(type=typed_type, analyse_result=result.response)


async def _analyze_resume_section(
    rtx: AnalyseContext,
    analysis_type: str,
    llm: BaseChatModel,
) -> SectionAnalysis:
    """이력서 분석 로직 (단순 정보 전달)"""
    typed_type = ResumeAnalysisType(analysis_type)
    prompt = get_analysis_prompt(analysis_type)
    chain = prompt | llm.with_structured_output(AiResponse, method="json_mode")
    
    job_info = rtx.job_info
    job_title = job_info.summary.splitlines()[0] if job_info.summary else job_info.company_name

    result = await chain.ainvoke({
        "job_title": job_title,
        "summary": job_info.summary or "내용 없음",
        "tech_stacks": ", ".join(job_info.tech_stacks) if job_info.tech_stacks else "정보 없음",
        "main_tasks": ", ".join(job_info.main_tasks) if job_info.main_tasks else "정보 없음",
        "qualifications": ", ".join(getattr(job_info, "qualifications", [])) or "정보 없음",
        "preferred_points": ", ".join(getattr(job_info, "preferred_points", [])) or "정보 없음",
        "doc_text": rtx.doc_text,
        "analysis_type": analysis_type,
    })

    if not isinstance(result, AiResponse):
        raise TypeError(f"Expected AiResponse but got {type(result)}")

    return SectionAnalysis(type=typed_type, analyse_result=result.response)


async def generate_report_node(
    state: AnalysisState, config: RunnableConfig, runtime: Runtime[AnalyseContext]
):
    """최종 레포트 생성 노드 (Reducer 이후) - LLM을 통한 종합 분석"""
    section_results = state["section_analyses"]

    logger.info(
        f"generate_report_node: Processing {len(section_results)} section analyses"
    )

    # 1. Config & Context 로드
    cfg = Configuration.from_runnable_config(config)
    rtx = runtime.context

    # 2. LLM 로드
    llm = load_chat_model(cfg.model_name, cfg.model_provider).with_structured_output(
        AiResponse, method="json_mode"
    )

    # 3. 문서 타입에 따른 프롬프트 선택
    doc_type = rtx.doc_type.value
    prompt = get_final_report_prompt(doc_type)

    # 4. 분석 결과 포맷팅
    analysis_results_text = _format_analysis_results(section_results)

    # 5. Job Info 준비
    job_info = rtx.job_info
    job_title = (
        job_info.summary.splitlines()[0] if job_info.summary else job_info.company_name
    )

    # 6. LLM 체인 실행
    chain = prompt | llm

    try:
        final_report = await chain.ainvoke(
            {
                "job_title": job_title,
                "main_tasks": (
                    ", ".join(job_info.main_tasks)
                    if job_info.main_tasks
                    else "정보 없음"
                ),
                "tech_stacks": (
                    ", ".join(job_info.tech_stacks)
                    if job_info.tech_stacks
                    else "정보 없음"
                ),
                "qualifications": (
                    ", ".join(getattr(job_info, "qualifications", []))
                    if getattr(job_info, "qualifications", None)
                    else "정보 없음"
                ),
                "preferred_points": (
                    ", ".join(getattr(job_info, "preferred_points", []))
                    if getattr(job_info, "preferred_points", None)
                    else "정보 없음"
                ),
                "analysis_results": analysis_results_text,
            }
        )

        # Type guard - ensure result is AiResponse
        if not isinstance(final_report, AiResponse):
            raise TypeError(f"Expected AiResponse but got {type(final_report)}")

        logger.info(f"Final report generated successfully for {doc_type}")

    except Exception as e:
        logger.error(f"Failed to generate final report with LLM: {e}")
        # Fallback: 간단한 요약 생성
        final_report = _create_fallback_report(section_results, doc_type)

    return {"overall_review": final_report.response}


def _format_analysis_results(section_results: List[SectionAnalysis]) -> str:
    """분석 결과를 LLM에 전달할 포맷으로 변환"""
    formatted_lines = []

    for idx, result in enumerate(section_results, 1):
        formatted_lines.append(f"\n## {idx}. {result.type}\n")
        formatted_lines.append(result.analyse_result)
        formatted_lines.append("\n" + "-" * 80 + "\n")

    return "\n".join(formatted_lines)


def _create_fallback_report(
    section_results: List[SectionAnalysis], doc_type: str
) -> AiResponse:
    """LLM 실패 시 사용할 Fallback 리포트"""
    summary_lines = [f"# {doc_type.upper()} 분석 결과\n"]

    for res in section_results:
        summary_lines.append(f"\n## {res.type}")
        summary_lines.append(res.analyse_result[:200] + "...\n")

    summary_lines.append("\n---\n**Note**: 자동 생성된 요약 리포트입니다.")

    return AiResponse(response="\n".join(summary_lines))
