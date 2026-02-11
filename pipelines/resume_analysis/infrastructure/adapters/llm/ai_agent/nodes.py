
import logging
from typing import Any, Dict, List

from langchain_core.runnables import RunnableConfig

from .....domain.models.document import DocumentType
from .....domain.models.report import SectionAnalysis
from .....domain.models.report import ResumeAnalysisType, PortfolioAnalysisType
from .state import AnalysisState
from langgraph.runtime import Runtime
from langgraph.types import Send, Command



from .configuration import AnalyseContext, Configuration
from .prompts import get_analysis_prompt, get_final_report_prompt
from .utils import load_chat_model

logger = logging.getLogger(__name__)


def plan_analysis(state: AnalysisState, runtime: Runtime[AnalyseContext]):
    target_doc_type = runtime.context.doc_type

    logger.info(f"PLAN: Analyzing {target_doc_type}")

    # execute_analysis_node에 analyse_type을 전달하여 병렬적으로 실행
    # Send로 실행되는 node의 State는 전체 그래프의 State와 분리됨
    if target_doc_type == DocumentType.RESUME:
        sends = [Send("execute_analysis_node", {"analyse_type":type.value}) for type in ResumeAnalysisType]
        return Command(goto=sends)
    elif target_doc_type == DocumentType.PORTFOLIO:
        sends = [Send("execute_analysis_node", {"analyse_type":type.value}) for type in PortfolioAnalysisType]
        return Command(goto=sends)


async def execute_analysis_node(input_state: dict[str,str], config: RunnableConfig, runtime: Runtime[AnalyseContext]):
    """
    단일 항목에 대한 분석을 수행하는 노드 (Parallel Worker)
    
    Args:
        input_state: SectionAnalysisState (Send API로 전달됨)
        config: RunnableConfig
    """
    # 1. 입력 검증
    analysis_type = input_state.get("analyse_type")
    if not analysis_type:
        raise ValueError("analysis_type is missing in execute_analysis_node input")

    logger.info(f"Analyzing {analysis_type}")

    # 2. Config & Context 로드
    cfg = Configuration.from_runnable_config(config)
    rtx = runtime.context
    
    # 3. LLM 로드
    llm = load_chat_model(cfg.model_name, cfg.model_provider)

    logger.info(f"[{cfg.model_name}] Analyzing Section: {analysis_type} ...")
    
    try:
        # 4. 분석 수행 (Helper Function 호출)
        result = await _analyze_single_section(rtx, analysis_type, llm)
        
        # 5. 결과 반환 (Main State에 병합될 구조)
        return {"section_analyses": [result]}
        
    except Exception as e:
        logger.info(f"Analysis Failed for {analysis_type}: {e}")
        return {"section_analyses": []} # 실패 시 빈 리스트 반환 (전체 프로세스는 계속됨)


async def _analyze_single_section(
    rtx: AnalyseContext,
    analysis_type: str,
    llm: Any
) -> SectionAnalysis:
    """단일 항목에 대한 분석 로직 (순수 함수)"""

    # 프롬프트 가져오기
    prompt = get_analysis_prompt(analysis_type)
    chain = prompt | llm

    # Job Title Fallback Logic
    job_info = rtx.job_info
    job_title = job_info.summary.splitlines()[0] if job_info.summary else job_info.company_name

    # LLM 실행
    response = await chain.ainvoke({
        "job_title": job_title,
        "summary": job_info.summary or "내용 없음",
        "tech_stacks": ", ".join(job_info.tech_stacks) if job_info.tech_stacks else "정보 없음",
        "main_tasks": ", ".join(job_info.main_tasks) if job_info.main_tasks else "정보 없음",
        "qualifications": getattr(job_info, 'qualifications', None) and ", ".join(job_info.qualifications) or "정보 없음",
        "preferred_points": getattr(job_info, 'preferred_points', None) and ", ".join(job_info.preferred_points) or "정보 없음",
        "doc_text": rtx.doc_text,
        "analysis_type": analysis_type
    })

    # 결과 매핑 - content에서 텍스트만 추출
    if isinstance(response.content, str):
        content = response.content
    elif isinstance(response.content, list):
        # content가 리스트인 경우, type이 'text'인 항목만 추출
        text_parts = [item.get('text', '') for item in response.content if isinstance(item, dict) and item.get('type') == 'text']
        content = ''.join(text_parts)
    else:
        content = str(response.content)

    return SectionAnalysis(
        type=analysis_type,
        analyse_result=content
    )

async def generate_report_node(state: AnalysisState, config: RunnableConfig, runtime: Runtime[AnalyseContext]):
    """최종 레포트 생성 노드 (Reducer 이후) - LLM을 통한 종합 분석"""
    section_results = state["section_analyses"]

    logger.info(f"generate_report_node: Processing {len(section_results)} section analyses")

    # 1. Config & Context 로드
    cfg = Configuration.from_runnable_config(config)
    rtx = runtime.context

    # 2. LLM 로드
    llm = load_chat_model(cfg.model_name, cfg.model_provider)

    # 3. 문서 타입에 따른 프롬프트 선택
    doc_type = rtx.doc_type.value
    prompt = get_final_report_prompt(doc_type)

    # 4. 분석 결과 포맷팅
    analysis_results_text = _format_analysis_results(section_results)

    # 5. Job Info 준비
    job_info = rtx.job_info
    job_title = job_info.summary.splitlines()[0] if job_info.summary else job_info.company_name

    # 6. LLM 체인 실행
    chain = prompt | llm

    try:
        response = await chain.ainvoke({
            "job_title": job_title,
            "main_tasks": ", ".join(job_info.main_tasks) if job_info.main_tasks else "정보 없음",
            "tech_stacks": ", ".join(job_info.tech_stacks) if job_info.tech_stacks else "정보 없음",
            "qualifications": getattr(job_info, 'qualifications', None) and ", ".join(job_info.qualifications) or "정보 없음",
            "preferred_points": getattr(job_info, 'preferred_points', None) and ", ".join(job_info.preferred_points) or "정보 없음",
            "analysis_results": analysis_results_text
        })

        # response.content에서 텍스트만 추출
        if isinstance(response.content, str):
            final_report = response.content
        elif isinstance(response.content, list):
            # content가 리스트인 경우, type이 'text'인 항목만 추출
            text_parts = [item.get('text', '') for item in response.content if isinstance(item, dict) and item.get('type') == 'text']
            final_report = ''.join(text_parts)
        else:
            final_report = str(response.content)

        logger.info(f"Final report generated successfully for {doc_type}")

    except Exception as e:
        logger.error(f"Failed to generate final report with LLM: {e}")
        # Fallback: 간단한 요약 생성
        final_report = _create_fallback_report(section_results, doc_type)

    return {"overall_review": final_report}


def _format_analysis_results(section_results: List[SectionAnalysis]) -> str:
    """분석 결과를 LLM에 전달할 포맷으로 변환"""
    formatted_lines = []

    for idx, result in enumerate(section_results, 1):
        formatted_lines.append(f"\n## {idx}. {result.type}\n")
        formatted_lines.append(result.analyse_result)
        formatted_lines.append("\n" + "-" * 80 + "\n")

    return "\n".join(formatted_lines)


def _create_fallback_report(section_results: List[SectionAnalysis], doc_type: str) -> str:
    """LLM 실패 시 사용할 Fallback 리포트"""
    summary_lines = [f"# {doc_type.upper()} 분석 결과\n"]

    for res in section_results:
        summary_lines.append(f"\n## {res.type}")
        summary_lines.append(res.analyse_result[:200] + "...\n")

    summary_lines.append("\n---\n**Note**: 자동 생성된 요약 리포트입니다.")

    return "\n".join(summary_lines)
