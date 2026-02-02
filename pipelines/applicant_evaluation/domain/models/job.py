from dataclasses import dataclass, field
from typing import List


@dataclass
class EvaluationCriteria:
    """평가 기준 (예: 직무 적합성, 성장 가능성 등)"""

    name: str
    description: str


@dataclass
class JobInfo:
    """채용 공고 핵심 정보"""

    company_name: str
    main_tasks: List[str]  # 주요 업무
    tech_stacks: List[str]  # 기술 스택
    summary: str  # 공고 요약

    # 지원자 평가기준 4가지
    evaluation_criteria: List[EvaluationCriteria] = field(default_factory=list)

    def validate(self):
        """JobInfo 데이터 유효성 검증"""
        if not self.company_name:
            raise ValueError("Company name must not be empty.")
        if not self.evaluation_criteria:
            raise ValueError("Evaluation criteria must not be empty.")
