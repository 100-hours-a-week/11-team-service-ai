from dataclasses import dataclass
from typing import List
from shared.schema.applicant import EvaluateResponse, CompetencyScore
from ..domain.models.report import AnalysisReport

class PipelineEvaluateResponse(EvaluateResponse):
    """
    Shared Schema를 상속받아 도메인 모델(Report)로부터 변환하는 로직을 추가한 DTO
    """
    @classmethod
    def from_domain(cls, report: AnalysisReport) -> "EvaluateResponse":
        """AnalysisReport(Domain) -> EvaluateResponse(DTO) 변환"""
        return cls(
            overall_score=report.overall_score,
            one_line_review=report.one_line_review,
            feedback_detail=report.feedback_detail,
            competency_scores=[
                CompetencyScore(
                    name=r.name, 
                    score=r.score, 
                    description=r.description
                ) for r in report.competency_scores
            ]
        )
