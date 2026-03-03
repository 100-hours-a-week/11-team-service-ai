from typing import List
from ..models.candidate import Candidate
from ..models.report import ComparisonReport, ComparisonMetric


class CandidateComparisonServiceError(Exception):
    """지원자 비교 서비스 관련 예외"""

    pass


class CandidateComparisonService:
    """
    지원자 비교 도메인 서비스
    두 지원자의 평가 결과를 대조하여 비교 리포트를 생성
    """

    @staticmethod
    def generate_comparison_report(
        my_candidate: Candidate,
        competitor_candidate: Candidate,
        strengths: str,
        weaknesses: str,
    ) -> ComparisonReport:
        """
        비교 리포트 생성
        내부적으로 비교 지표를 산출하고 강점/약점 분석을 통합하여 리포트 반환
        """
        # 1. 비교 가능 여부 검증
        CandidateComparisonService.validate_comparison_eligibility(
            my_candidate, competitor_candidate
        )

        # 2. 비교 지표 생성 (create_comparison_metrics 재사용)
        metrics = CandidateComparisonService.create_comparison_metrics(
            my_candidate, competitor_candidate
        )

        return ComparisonReport.create(
            metrics=metrics, strengths=strengths, weaknesses=weaknesses
        )

    @staticmethod
    def validate_comparison_eligibility(
        my_candidate: Candidate, competitor_candidate: Candidate
    ):
        """
        비교 수행 가능 여부 검증
        - 두 지원자 모두 평가 결과가 있는지 확인
        """
        if not my_candidate.is_ready_for_comparison():
            raise CandidateComparisonServiceError(
                "내 지원자가 비교 가능한 상태가 아닙니다."
            )

        if not competitor_candidate.is_ready_for_comparison():
            raise CandidateComparisonServiceError(
                "비교 대상 지원자가 비교 가능한 상태가 아닙니다."
            )

    @staticmethod
    def create_comparison_metrics(
        my_candidate: Candidate, competitor_candidate: Candidate
    ) -> List[ComparisonMetric]:
        """
        두 지원자의 역량 점수를 비교 지표로 변환
        역량명 기준으로 매칭하여 ComparisonMetric 생성
        """
        my_scores = {
            score.name: score.score
            for score in my_candidate.evaluation.competency_scores
        }
        competitor_scores = {
            score.name: score.score
            for score in competitor_candidate.evaluation.competency_scores
        }

        # 공통 역량 기준으로 매칭
        common_metrics = set(my_scores.keys()) & set(competitor_scores.keys())

        if not common_metrics:
            raise CandidateComparisonServiceError(
                "두 지원자 간 공통 평가 지표가 없습니다."
            )

        metrics = [
            ComparisonMetric(
                name=metric_name,
                my_score=my_scores[metric_name],
                competitor_score=competitor_scores[metric_name],
            )
            for metric_name in sorted(common_metrics)
        ]

        return metrics
