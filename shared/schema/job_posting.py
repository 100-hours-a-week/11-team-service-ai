from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field


class JobPostingAnalyzeRequest(BaseModel):
    url: str = Field(..., description="분석할 채용 공고의 URL")


class RecruitmentPeriod(BaseModel):
    start_date: Optional[date] = Field(None, description="채용 시작일")
    end_date: Optional[date] = Field(None, description="채용 종료일")


class JobPostingAnalyzeResponse(BaseModel):
    job_posting_id: int = Field(..., description="채용 공고 ID (DB 식별자)")
    is_existing: bool = Field(..., description="기존 데이터 존재 여부")
    company_name: str = Field(..., description="회사명")
    job_title: str = Field(..., description="공고 제목 (직무명)")
    main_responsibilities: List[str] = Field(..., description="주요 업무 리스트")
    required_skills: List[str] = Field(..., description="필요 기술 스택 리스트")
    recruitment_status: str = Field(..., description="채용 진행 상태")
    recruitment_period: Optional[RecruitmentPeriod] = Field(
        None, description="채용 기간"
    )
    ai_summary: str = Field(..., description="AI가 요약한 공고 핵심 내용")
    evaluation_criteria: Optional[List[dict]] = Field(
        default=[], description="평가 기준 리스트"
    )


class JobPostingDeleteResponse(BaseModel):
    deleted_id: int = Field(..., description="삭제된 채용 공고 ID")
