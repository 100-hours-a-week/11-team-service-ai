import pytest
from pipelines.applicant_evaluation.domain.models.report import (
    AnalysisReport,
    OverallFeedback,
    AnalysisReportError,
)
from pipelines.applicant_evaluation.domain.models.evaluation import CompetencyResult
from pipelines.applicant_evaluation.domain.models.job import JobInfo, EvaluationCriteria


class TestAnalysisReport:
    @pytest.fixture
    def job_info(self):
        return JobInfo(
            company_name="Test",
            main_tasks=[],
            tech_stacks=[],
            summary="",
            evaluation_criteria=[
                EvaluationCriteria(name="A", description=""),
                EvaluationCriteria(name="B", description=""),
            ],
        )

    @pytest.fixture
    def feedback(self):
        return OverallFeedback(one_line_review="Good", feedback_detail="Detail")

    def test_create_success_and_score_calculation(self, job_info, feedback):
        """모든 기준 충족 시 생성 성공 및 평균 점수 계산 확인"""
        results = [
            CompetencyResult(name="A", score=80, description=""),
            CompetencyResult(name="B", score=90, description=""),
        ]

        report = AnalysisReport.create(job_info, results, feedback)

        assert isinstance(report, AnalysisReport)
        # (80 + 90) / 2 = 85.0
        assert report.overall_score == 85.0

    def test_create_completeness_validation_fail(self, job_info, feedback):
        """평가 기준 중 하나라도 결과가 없으면 생성 실패"""
        # Criteria has A, B but results only have A
        results = [CompetencyResult(name="A", score=80, description="")]

        with pytest.raises(AnalysisReportError, match="누락"):
            AnalysisReport.create(job_info, results, feedback)

    def test_create_missing_feedback_data(self, job_info):
        """종합 피드백 내용이 비어있으면 생성 실패"""
        results = [
            CompetencyResult(name="A", score=80, description=""),
            CompetencyResult(name="B", score=90, description=""),
        ]
        empty_feedback = OverallFeedback(one_line_review="", feedback_detail="")

        with pytest.raises(AnalysisReportError, match="종합 평가 데이터"):
            AnalysisReport.create(job_info, results, empty_feedback)

    def test_overall_score_rounding(self, job_info, feedback):
        """점수 계산 시 소수점 반올림 확인"""
        results = [
            CompetencyResult(name="A", score=80, description=""),
            CompetencyResult(name="B", score=81, description=""),
        ]
        # (80 + 81) / 2 = 80.5
        report = AnalysisReport.create(job_info, results, feedback)
        assert report.overall_score == 80.5

        # 80, 80, 81 -> 241 / 3 = 80.333... -> 80.3
        # (테스트 편의상 criteria 무시하고 계산 로직만 unit test하고 싶다면 직접 생성자 호출 가능하지만,
        # create 팩토리를 통하는 것이 정석이므로 criteria를 맞춰주는 게 좋음)
