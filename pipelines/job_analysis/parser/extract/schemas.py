from typing import List, Optional
from pydantic import BaseModel, Field


class EvaluationCriteriaItem(BaseModel):
    name: str = Field(..., description="평가 기준명 (예: '직무 적합성')")
    description: str = Field(..., description="해당 기준에 대한 설명")


class ExtractedJobData(BaseModel):
    """채용 공고 텍스트에서 추출할 구조화된 데이터"""

    company_name: str = Field(..., description="공고에 명시된 정확한 회사명")
    job_title: str = Field(..., description="공고 제목 또는 모집 직무명")

    main_tasks: List[str] = Field(
        default_factory=list,
        description="주요 업무 내용. 각 항목을 명확한 문장으로 분리하여 추출",
    )

    requirements: List[str] = Field(
        default_factory=list,
        description="자격 요건 및 필수 역량 (경력, 학력, 필수 기술 등)",
    )

    preferred: List[str] = Field(
        default_factory=list, description="우대 사항 (자격증, 경험, 언어 능력 등)"
    )

    tech_stacks: List[str] = Field(
        default_factory=list,
        description="언급된 기술 스택, 프레임워크, 도구 (예: Python, React, AWS). 원문 그대로가 아니라 가능한 영어 표준 명칭으로 추출",
    )

    start_date: Optional[str] = Field(None, description="채용 시작일 (YYYY-MM-DD).")

    end_date: Optional[str] = Field(
        None,
        description="채용 종료일/마감일 (YYYY-MM-DD). 상시채용인 경우 None 또는 '9999-12-31'",
    )

    ai_summary: str = Field(..., description="공고 전체에 대한 3줄 이내의 핵심 요약")

    evaluation_criteria: List[EvaluationCriteriaItem] = Field(
        default_factory=list,
        description="채용 평가 기준 (예: [{'name': '직무 적합성', 'description': '...'}, ...])",
    )
