from typing import List
from ...domain.models.report import ComparisonReport
from shared.schema.applicant import (
    CompareResponse,
    ComparisonMetric as SchemaComparisonMetric,
)


class ComparisonMapper:
    """
    비교 결과 도메인 모델(ComparisonReport)을 API 응답 스키마로 변환하는 매퍼
    """

    @staticmethod
    def to_compare_response(report: ComparisonReport) -> CompareResponse:
        """
        지원자 비교 결과를 API 응답 스키마로 변환

        Args:
            report: 도메인 비교 리포트

        Returns:
            CompareResponse: API 응답 스키마
        """
        # 도메인 ComparisonMetric을 스키마 ComparisonMetric으로 변환
        metrics: List[SchemaComparisonMetric] = [
            SchemaComparisonMetric(
                name=metric.name,
                my_score=metric.my_score,
                competitor_score=metric.competitor_score,
            )
            for metric in report.comparison_metrics
        ]

        return CompareResponse(
            comparison_metrics=metrics,
            strengths_report=report.strengths_report,
            weaknesses_report=report.weaknesses_report,
        )
