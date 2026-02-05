from pydantic import BaseModel, Field, field_validator


class CompetencyResult(BaseModel):
    """개별 역량 평가 결과 (AI 분석 결과 1건)"""

    name: str = Field(description="역량 항목명 (criteria_name)")
    score: float = Field(description="역량 점수 (0-100)")
    description: str = Field(description="역량 평가 상세 (reason)")

    # 점수 유효성 검증 로직 구현
    @field_validator("score")
    @classmethod
    def validate_score(cls, v: float) -> float:
        if not (0 <= v <= 100):
            raise ValueError("Score must be between 0 and 100")
        return v
