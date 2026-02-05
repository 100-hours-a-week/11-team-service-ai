import pytest
from pydantic import ValidationError
from pipelines.applicant_evaluation.domain.models.job import JobInfo, EvaluationCriteria


class TestJobInfo:
    @pytest.fixture
    def valid_criteria(self):
        return [EvaluationCriteria(name="Criteria1", description="desc")]

    def test_validation_success(self, valid_criteria):
        """정상적인 데이터로 생성 시 에러 없음"""
        # Should not raise any exception on init
        JobInfo(
            company_name="Kakao",
            main_tasks=["Task1"],
            tech_stacks=["Python"],
            summary="Good Job",
            evaluation_criteria=valid_criteria,
        )

    def test_validation_missing_company_name(self, valid_criteria):
        """회사명이 비어있으면 에러 발생"""
        # Construction with empty company name should fail due to @model_validator
        with pytest.raises(ValidationError):
            JobInfo(
                company_name="",  # Empty
                main_tasks=["Task1"],
                tech_stacks=["Python"],
                summary="Job",
                evaluation_criteria=valid_criteria,
            )

    def test_validation_missing_criteria(self):
        """평가 기준이 없으면 에러 발생"""
        with pytest.raises(ValidationError):
            JobInfo(
                company_name="Kakao",
                main_tasks=["Task1"],
                tech_stacks=["Python"],
                summary="Job",
                evaluation_criteria=[],  # Empty
            )
