import logging

from langgraph.graph import StateGraph, START, END

from .....domain.interface.adapter_interfaces import AnalystAgent
from .....domain.models.job import JobInfo
from .....domain.models.document import DocumentType
from .....domain.models.report import AnalysisReport

# Import local modules (relative)
from .configuration import AnalyseContext
from .state import AnalysisState
from .nodes import execute_analysis_node, generate_report_node, plan_analysis

logger = logging.getLogger(__name__)


class LLMAnalyst(AnalystAgent):
    """
    LangGraph 기반의 AI 분석 에이전트 (Map-Reduce Orchestrator)
    """

    def __init__(self, model_name: str = "gpt-4o", model_provider: str = "openai"):
        self.model_name = model_name
        self.model_provider = model_provider

    async def run_analysis(
        self,
        job_info: JobInfo,
        document_text: str,
        doc_type: DocumentType = DocumentType.RESUME,
    ) -> AnalysisReport:
        """
        문서 분석 전체 파이프라인(LangGraph) 실행
        """

        builder = StateGraph(state_schema=AnalysisState, context_schema=AnalyseContext)
        builder.add_node("plan_analysis", plan_analysis)  # type: ignore[call-overload]
        builder.add_node("execute_analysis_node", execute_analysis_node)  # type: ignore[call-overload]
        builder.add_node("generate_report_node", generate_report_node)  # type: ignore[call-overload]

        builder.add_edge(START, "plan_analysis")
        builder.add_edge("execute_analysis_node", "generate_report_node")
        builder.add_edge("generate_report_node", END)

        graph = builder.compile()

        # 실행 설정 (모델 변경 등)
        config = {
            "configurable": {
                "model_provider": self.model_provider,
                "model_name": self.model_name,
            }
        }

        context_data = AnalyseContext(
            job_info=job_info, doc_type=doc_type, doc_text=document_text
        )

        # 그래프 실행
        final_state = await graph.ainvoke(
            {"section_analyses": [], "overall_review": ""},  # type: ignore[arg-type]
            config=config,  # type: ignore[arg-type]
            context=context_data,  # type: ignore[call-arg]
        )

        return AnalysisReport.create(
            results=final_state["section_analyses"],
            overall_review=final_state["overall_review"],
        )
