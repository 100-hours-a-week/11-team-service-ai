from dataclasses import dataclass, field
from typing import List, Set
from .evaluation import CompetencyResult
from .job import JobInfo

# 임시 예외 클래스 정의 (또는 별도 예외 파일 import)
class AnalysisReportError(Exception):
    pass

@dataclass
class OverallFeedback:
    """종합 평가 결과 VO"""
    one_line_review: str    # AI 한 줄 평가
    feedback_detail: str    # 상세 피드백 (강점 및 보완점 통합)

@dataclass
class AnalysisReport:
    """
    최종 분석 리포트 (Aggregate Root)
    """
    competency_scores: List[CompetencyResult] # 세부 역량별 점수 리스트
    
    one_line_review: str    # AI 한 줄 평가
    feedback_detail: str    # 상세 피드백 (강점 및 보완점 통합)

    @classmethod
    def create(
        cls, 
        job_info: JobInfo, 
        results: List[CompetencyResult], 
        feedback: OverallFeedback
    ) -> 'AnalysisReport':
        """
        팩토리 메서드: 도메인 규칙(검증)을 통과한 유효한 리포트 객체만 생성
        """
        # 1. 정합성 검증 (모든 평가 기준 충족 여부)
        cls._validate_completeness(job_info, results)
        
        # 2. 필수 데이터 검증
        if not feedback.one_line_review or not feedback.feedback_detail:
             raise AnalysisReportError("종합 평가 데이터(one_line_review, feedback_detail)가 누락되었습니다.")

        # 3. 객체 생성
        return cls(
            competency_scores=results,
            one_line_review=feedback.one_line_review,
            feedback_detail=feedback.feedback_detail
        )

    @staticmethod
    def _validate_completeness(job_info: JobInfo, results: List[CompetencyResult]):
        """모든 평가 기준이 누락 없이 평가되었는지 검사"""
        required_criteria: Set[str] = {c.name for c in job_info.evaluation_criteria}
        evaluated_criteria: Set[str] = {r.name for r in results}
        
        missing = required_criteria - evaluated_criteria
        if missing:
            raise AnalysisReportError(f"일부 평가 기준에 대한 결과가 누락되었습니다: {missing}")

    @property
    def overall_score(self) -> float:
        """
        종합 점수 계산 로직 (도메인 로직)
        """
        if not self.competency_scores:
            return 0.0
        
        total = sum(item.score for item in self.competency_scores)
        average = total / len(self.competency_scores)
        
        return round(average, 1)
