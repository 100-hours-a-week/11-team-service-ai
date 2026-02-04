from typing import List, Optional
from pydantic import BaseModel


class EvaluationCriteriaItem(BaseModel):
    name: str
    description: str


class ExtractedJobData(BaseModel):
    """추출된 채용 공고 데이터 (Domain Model)"""

    company_name: str
    job_title: str
    main_tasks: List[str]
    tech_stacks: List[str]
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    ai_summary: Optional[str] = None
    evaluation_criteria: List[EvaluationCriteriaItem] = []
