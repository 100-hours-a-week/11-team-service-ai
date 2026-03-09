import operator
from typing import Annotated, List
from typing_extensions import TypedDict
from pydantic import BaseModel, Field


# 1. 기술 정보를 담는 클래스
class TechInfo(BaseModel):
    subject: str = Field(description="기술명 또는 주제 (예: Redis)")
    content: str = Field(description="파악된 기술적 세부 정보, 활용 맥락 등")


# 2. 기술 평가 요소를 담는 클래스
class TechCompetencyFactor(BaseModel):
    factor_name: str = Field(description="평가 요소명 (예: 대규모 트래픽 처리 경험)")
    content: str = Field(description="요구되는 수준이나 지식")


# 상태 관리 (Graph State)
class ResearcherState(TypedDict):
    tech_info: Annotated[List[TechInfo], operator.add]
    tech_competency_factors: Annotated[List[TechCompetencyFactor], operator.add]


class SubResearcherState(TypedDict):
    keyword: str  # 기술명 또는 주제 (예: Redis)
    result: str  # 파악된 기술적 세부 정보, 활용 맥락 등
    search_score: float  # 벡터 DB 검색 후의 유사도 / 임계 점수
    is_valid: bool  # AI 적합성 판별 결과 (유효함/유효하지 않음)
