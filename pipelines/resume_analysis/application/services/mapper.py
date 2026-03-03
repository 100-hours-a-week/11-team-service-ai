from ...domain.models.report import (
    AnalysisReport,
    ResumeAnalysisType,
    PortfolioAnalysisType,
)
from shared.schema.document import ResumeAnalyzeResponse, PortfolioAnalyzeResponse


class ReportMapper:
    """
    분석 결과 도메인 모델(AnalysisReport)을 API 응답 스키마로 변환하는 매퍼
    """

    @staticmethod
    def to_resume_response(report: AnalysisReport) -> ResumeAnalyzeResponse:
        """
        이력서 분석 결과 매핑
        """
        job_fit = ""
        exp_clarity = ""
        readability = ""

        # 도메인 모델(report.py)의 AnalysisType과 매핑
        for section in report.section_analyses:
            if section.type == ResumeAnalysisType.JOB_FIT:
                job_fit = section.analyse_result
            elif section.type == ResumeAnalysisType.EXPERIENCE_CLARITY:
                exp_clarity = section.analyse_result
            elif section.type == ResumeAnalysisType.READABILITY:
                readability = section.analyse_result

        return ResumeAnalyzeResponse(
            ai_analysis_report=report.overall_review,
            job_fit_score=job_fit,
            experience_clarity_score=exp_clarity,
            readability_score=readability,
        )

    @staticmethod
    def to_portfolio_response(report: AnalysisReport) -> PortfolioAnalyzeResponse:
        """
        포트폴리오 분석 결과 매핑
        """
        problem_solving = ""
        contribution = ""
        tech_depth = ""

        for section in report.section_analyses:
            if section.type == PortfolioAnalysisType.PROBLEM_SOLVING:
                problem_solving = section.analyse_result
            elif section.type == PortfolioAnalysisType.CONTRIBUTION_CLARITY:
                contribution = section.analyse_result
            elif section.type == PortfolioAnalysisType.TECHNICAL_DEPTH:
                tech_depth = section.analyse_result

        return PortfolioAnalyzeResponse(
            ai_analysis_report=report.overall_review,
            problem_solving_score=problem_solving,
            contribution_clarity_score=contribution,
            technical_depth_score=tech_depth,
        )
