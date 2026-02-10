import logging
from typing import List

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


class MockAnalyst(AnalystAgent):
    """
    개발 및 테스트용 Mock Agent
    실제 LLM 호출 없이 고정된 더미 데이터를 반환합니다.
    """

    async def run_analysis(
        self,
        job_info: JobInfo,
        document_text: str,
        doc_type: DocumentType = DocumentType.RESUME,
    ) -> AnalysisReport:
        logger.info(f"[Mock] run_analysis called for doc_type: {doc_type}")
        
        if doc_type == DocumentType.RESUME:
            return AnalysisReport(
                section_analyses=[
                    SectionAnalysis(
                        type=ResumeAnalysisType.JOB_FIT, 
                        analyse_result="[Mock] 이력서 직무 적합도: 매우 적합합니다."
                    ),
                    SectionAnalysis(
                        type=ResumeAnalysisType.EXPERIENCE_CLARITY, 
                        analyse_result="[Mock] 경력 기술이 명확하고 성과가 잘 드러납니다."
                    ),
                    SectionAnalysis(
                        type=ResumeAnalysisType.READABILITY, 
                        analyse_result="[Mock] 가독성이 좋고 핵심 정보 파악이 용이합니다."
                    )
                ],
                overall_review="[Mock] Resume: 전반적으로 직무에 적합하며 경력 기술이 훌륭한 지원자입니다."
            )
        
        elif doc_type == DocumentType.PORTFOLIO:
            return AnalysisReport(
                section_analyses=[
                    SectionAnalysis(
                        type=PortfolioAnalysisType.PROBLEM_SOLVING, 
                        analyse_result="[Mock] 문제 해결 과정이 논리적으로 잘 서술되었습니다."
                    ),
                    SectionAnalysis(
                        type=PortfolioAnalysisType.CONTRIBUTION_CLARITY, 
                        analyse_result="[Mock] 프로젝트 내 역할과 기여도가 명확합니다."
                    ),
                    SectionAnalysis(
                        type=PortfolioAnalysisType.TECHNICAL_DEPTH, 
                        analyse_result="[Mock] 사용한 기술에 대한 이해도가 높습니다."
                    )
                ],
                overall_review="[Mock] Portfolio: 기술적 깊이가 있고 문제 해결 능력이 돋보이는 포트폴리오입니다."
            )
            
        else:
            # Fallback for unknown types
             return AnalysisReport(
                section_analyses=[],
                overall_review="[Mock] 알 수 없는 문서 타입입니다."
            )
