from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

class CandidateError(Exception):
    """지원자 도메인 관련 예외"""

    pass

class ApplicantDocuments(BaseModel):
    """한 지원자의 특정 공고에 대한 전체 제출 서류"""

    parsed_resume: str = Field(
        default=None, description="파싱된 이력서 데이터"
    )
    parsed_portfolio: Optional[str] = Field(
        default=None, description="파싱된 포트폴리오 데이터"
    )

class CompetencyScore(BaseModel):
    """개별 역량 평가 점수"""

    name: str = Field(description="역량 항목명")
    score: float = Field(description="역량 점수 (0-100)")
    feedback: str = Field(description="역량 평가 상세 피드백")

    @field_validator("score")
    @classmethod
    def validate_score(cls, v: float) -> float:
        if not (0 <= v <= 100):
            raise ValueError("Score must be between 0 and 100")
        return v


class EvaluationResult(BaseModel):
    """
    서류 평가 결과 (Internal Model)
    특정 공고 기준에 따라 AI가 분석한 데이터
    """
    competency_scores: List[CompetencyScore] = Field(
        description="세부 역량별 점수 리스트"
    )
    one_line_review: str = Field(description="AI 한 줄 평가")
    feedback_detail: str = Field(description="상세 피드백 (강점 및 보완점)")

    @property
    def overall_score(self) -> float:
        """종합 점수 계산"""
        if not self.competency_scores:
            return 0.0

        total = sum(score.score for score in self.competency_scores)
        average = total / len(self.competency_scores)

        return round(average, 1)



class Candidate(BaseModel):
    """
    지원자 Aggregate Root
    지원자의 서류와 평가 결과를 관리하는 중심 엔티티
    """

    documents: ApplicantDocuments = Field(description="제출 서류 (이력서, 포트폴리오)")
    evaluation: EvaluationResult = Field(description="서류 평가 결과")

    def is_ready_for_comparison(self) -> bool:
        """비교 가능한 상태인지 확인 (서류 + 평가 결과 모두 필요)"""
        
        # 1. 서류: 이력서가 파싱되어 있는지 확인 (포트폴리오는 옵션일 수 있음)
        documents_ready = bool(self.documents and self.documents.parsed_resume)
        
        # 2. 평가: 평가 결과 객체가 있고, 검사 점수 리스트가 비어있지 않은지 확인
        evaluation_ready = bool(self.evaluation and self.evaluation.competency_scores)
        
        return documents_ready and evaluation_ready