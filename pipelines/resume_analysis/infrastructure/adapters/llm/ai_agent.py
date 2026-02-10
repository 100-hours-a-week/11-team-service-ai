import logging
from typing import List, Literal, TypedDict

from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END

from ....domain.interface.adapter_interfaces import AnalystAgent
from ....domain.models.job import JobInfo
from ....domain.models.document import DocumentType
from ....domain.models.report import (
    AnalysisReport, 
    SectionAnalysis, 
    ResumeAnalysisType, 
    PortfolioAnalysisType
)

logger = logging.getLogger(__name__)


# --- LangGraph State Definition ---
class AnalysisState(TypedDict):
    job_info: JobInfo
    document_text: str
    doc_type: DocumentType
    
    # Intermediate results
    section_analyses: List[SectionAnalysis]
    overall_review: str


class LLMAnalyst(AnalystAgent):
    """
    LangGraph 기반의 AI 분석 에이전트 구현체
    """

    def __init__(self, llm: BaseChatModel):
        self.llm = llm
        self.workflow = self._build_workflow()

    def _build_workflow(self):
        """Build the LangGraph workflow"""
        workflow = StateGraph(AnalysisState)

        # Add Nodes
        workflow.add_node("analyze_sections", self._analyze_sections_node)
        workflow.add_node("synthesize_report", self._synthesize_report_node)

        # Define Edges
        workflow.set_entry_point("analyze_sections")
        workflow.add_edge("analyze_sections", "synthesize_report")
        workflow.add_edge("synthesize_report", END)

        return workflow.compile()

    async def run_analysis(
        self,
        job_info: JobInfo,
        document_text: str,
        doc_type: DocumentType = DocumentType.RESUME,
    ) -> AnalysisReport:
        """
        문서 분석 전체 파이프라인(LangGraph) 실행
        """
        initial_state = AnalysisState(
            job_info=job_info,
            document_text=document_text,
            doc_type=doc_type,
            section_analyses=[],
            overall_review=""
        )

        try:
            # Run the graph
            final_state = await self.workflow.ainvoke(initial_state)
            
            return AnalysisReport.create(
                results=final_state["section_analyses"],
                overall_review=final_state["overall_review"]
            )
            
        except Exception as e:
            logger.error(f"Analysis Pipeline Failed: {e}")
            # Fallback for error handling
            raise e

    # --- Node Implementations ---

    async def _analyze_sections_node(self, state: AnalysisState):
        """
        각 분석 영역별(직무 적합도 등) 상세 분석 수행
        """
        doc_type = state["doc_type"]
        job_info = state["job_info"]
        text = state["document_text"]

        target_types = self._get_analysis_criteria(doc_type)

        results = []
        # TODO: Parallel execution using asyncio.gather for performance
        for analysis_type in target_types:
            result = await self._generate_section_analysis(job_info, text, analysis_type, doc_type)
            results.append(result)

        return {"section_analyses": results}

    async def _synthesize_report_node(self, state: AnalysisState):
        """
        전체 분석 결과를 바탕으로 종합 리뷰 생성
        """
        section_results = state["section_analyses"]
        job_info = state["job_info"]

        prompt = ChatPromptTemplate.from_template(
            """
            You are an expert HR Recruiter. 
            Based on the following detailed section analyses of a candidate for the position of {job_title},
            write a comprehensive overall review (summary).
            
            Job Description Summary: {job_summary}
            
            Section Analyses:
            {section_analyses}
            
            Strictly write the overall review in Korean, summarizing the candidate's strengths and weaknesses.
            """
        )
        
        chain = prompt | self.llm
        
        # Prepare inputs
        sections_text = "\n".join([f"[{r.type}] {r.analyse_result}" for r in section_results])
        
        response = await chain.ainvoke({
            "job_title": job_info.title,
            "job_summary": job_info.summary or str(job_info.requirements),
            "section_analyses": sections_text
        })

        return {"overall_review": response.content}

    async def _generate_section_analysis(
        self, job_info: JobInfo, text: str, analysis_type: str, doc_type: DocumentType
    ) -> SectionAnalysis:
        """
        개별 섹션 분석 (LLM 호출)
        """
        prompt = self._get_section_prompt(doc_type)
        
        chain = prompt | self.llm
        
        response = await chain.ainvoke({
            "criteria": analysis_type,
            "job_title": job_info.title,
            "text": text[:15000] # Truncate if too long
        })
        
        return SectionAnalysis(
            type=analysis_type,
            analyse_result=response.content
        )

    # --- Helper Methods (Strategy Pattern alternative) ---

    def _get_analysis_criteria(self, doc_type: DocumentType) -> List[str]:
        """문서 타입에 따른 분석 기준 목록 반환"""
        if doc_type == DocumentType.RESUME:
            return [
                ResumeAnalysisType.JOB_FIT,
                ResumeAnalysisType.EXPERIENCE_CLARITY,
                ResumeAnalysisType.READABILITY
            ]
        elif doc_type == DocumentType.PORTFOLIO:
            return [
                PortfolioAnalysisType.PROBLEM_SOLVING,
                PortfolioAnalysisType.CONTRIBUTION_CLARITY,
                PortfolioAnalysisType.TECHNICAL_DEPTH
            ]
        else:
            return []

    def _get_section_prompt(self, doc_type: DocumentType) -> ChatPromptTemplate:
        """문서 타입에 따른 섹션 분석 프롬프트 반환"""
        # 현재는 둘 다 비슷한 포맷을 사용하지만, 필요 시 분리 가능
        if doc_type == DocumentType.RESUME:
            return ChatPromptTemplate.from_template(
                """
                You are an expert Resume Analyst.
                Analyze the RESUME excerpt based on the criteria: {criteria}.
                Target Job: {job_title}
                
                RESUME Text (Excerpt):
                {text}
                
                Provide a detailed analysis in Korean. Focus on qualitative assessment and evidence from the text.
                """
            )
        elif doc_type == DocumentType.PORTFOLIO:
             return ChatPromptTemplate.from_template(
                """
                You are an expert Portfolio Reviewer.
                Analyze the PORTFOLIO excerpt based on the criteria: {criteria}.
                Target Job: {job_title}
                
                PORTFOLIO Text (Excerpt):
                {text}
                
                Provide a detailed analysis in Korean. Focus on technical depth, problem-solving process, and contribution.
                """
            )
        else:
            # Fallback generic prompt
            return ChatPromptTemplate.from_template(
                """
                Analyze the following document text based on the criteria: {criteria}
                Target Job: {job_title}
                
                Document Text:
                {text}
                
                Provide a detailed analysis in Korean.
                """
            )
