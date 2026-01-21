from typing import List

from pydantic import BaseModel, Field


# 3.2 지원자 평가
class EvaluateRequest(BaseModel):
    user_id: str = Field(..., description="평가할 사용자 ID")
    job_posting_id: str = Field(..., description="지원할 채용 공고 ID")


class CompetencyScore(BaseModel):
    name: str = Field(..., description="역량 항목명")
    score: float = Field(..., description="역량 점수")
    description: str = Field(..., description="역량 평가 상세")


class EvaluateResponse(BaseModel):
    overall_score: float = Field(..., description="종합 직무 적합도 점수 (0-100)")
    competency_scores: List[CompetencyScore] = Field(..., description="세부 역량별 점수 리스트")
    one_line_review: str = Field(..., description="AI 한 줄 평가")
    feedback_detail: str = Field(..., description="상세 피드백 (강점 및 보완점 통합)")


# 3.3 지원자 비교
class CompareRequest(BaseModel):
    job_posting_id: str = Field(..., description="비교 기준이 되는 채용 공고 ID")
    user_id: str = Field(..., description="본인(사용자) ID")
    competitor: str = Field(..., description="비교 대상(경쟁자) ID")


class ComparisonMetric(BaseModel):
    name: str = Field(..., description="비교 항목명")
    my_score: float = Field(..., description="본인 점수")
    competitor_score: float = Field(..., description="경쟁자 점수")


class CompareResponse(BaseModel):
    comparison_metrics: List[ComparisonMetric] = Field(..., description="비교 지표 리스트")
    strengths_report: str = Field(..., description="경쟁 우위 요소 요약")
    weaknesses_report: str = Field(..., description="보완 필요 요소 요약")
