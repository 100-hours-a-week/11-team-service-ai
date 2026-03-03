from typing import List
from pydantic import BaseModel, Field, field_validator


class ComparisonReportError(Exception):
    """비교 리포트 관련 예외"""

    pass


class ComparisonMetric(BaseModel):
    """개별 평가 지표별 비교 점수"""

    name: str = Field(description="평가 지표명 (예: 기술 스택 숙련도, 프로젝트 복잡도)")
    my_score: float = Field(description="내 지원자(선택한 지원자) 점수")
    competitor_score: float = Field(description="비교 대상 지원자 점수")

    @field_validator("my_score", "competitor_score")
    @classmethod
    def validate_score(cls, v: float) -> float:
        if not (0 <= v <= 100):
            raise ValueError("Score must be between 0 and 100")
        return v


class ComparisonReport(BaseModel):
    """
    지원자 비교 결과 (Output Model)
    두 지원자를 평가 지표별로 대조한 최종 리포트
    """

    comparison_metrics: List[ComparisonMetric] = Field(
        description="개별 평가 지표별 비교 점수 리스트"
    )

    strengths_report: str = Field(
        description="내 지원자의 강점 (상대 지원자 대비 우수한 점)"
    )
    weaknesses_report: str = Field(
        description="내 지원자의 약점 (상대 지원자 대비 부족한 점)"
    )

    @classmethod
    def create(
        cls,
        metrics: List[ComparisonMetric],
        strengths: str,
        weaknesses: str,
    ) -> "ComparisonReport":
        """
        팩토리 메서드: 도메인 규칙을 통과한 유효한 비교 리포트 생성
        """
        if not metrics:
            raise ComparisonReportError("비교 지표가 비어있습니다.")

        if not strengths:
            raise ComparisonReportError("강점 리포트가 누락되었습니다.")

        if not weaknesses:
            raise ComparisonReportError("약점 리포트가 누락되었습니다.")

        return cls(
            comparison_metrics=metrics,
            strengths_report=strengths,
            weaknesses_report=weaknesses,
        )
