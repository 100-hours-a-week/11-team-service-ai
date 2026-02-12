from typing import List
from pydantic import BaseModel, Field, model_validator


class EvaluationCriteria(BaseModel):
    """평가 기준 (예: 직무 적합성, 성장 가능성 등)"""

    name: str = Field(description="평가 기준 명")
    description: str = Field(description="평가 기준 상세 설명")


class JobInfo(BaseModel):
    """채용 공고 핵심 정보"""

    job_posting_id: str = Field(description="공고 고유 ID")
    company_name: str = Field(description="회사명")
    main_tasks: List[str] = Field(description="주요 업무 리스트")
    tech_stacks: List[str] = Field(description="기술 스택 리스트")
    summary: str = Field(description="공고 요약")

    evaluation_criteria: List[EvaluationCriteria] = Field(
        default_factory=list, description="평가 기준 리스트"
    )

    @model_validator(mode="after")
    def validate_job_info(self) -> "JobInfo":
        """JobInfo 데이터 유효성 검증"""
        if not self.job_posting_id:
            raise ValueError("Job posting ID must not be empty.")
        if not self.company_name:
            raise ValueError("Company name must not be empty.")
        if not self.evaluation_criteria:
            raise ValueError("Evaluation criteria must not be empty.")
        return self
