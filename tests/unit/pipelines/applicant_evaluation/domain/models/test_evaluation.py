import pytest
from pydantic import ValidationError
from pipelines.applicant_evaluation.domain.models.evaluation import CompetencyResult


class TestCompetencyResult:
    def test_score_validation_valid(self):
        """0 ~ 100 사이의 점수는 유효함"""
        # Boundary: 0
        # Boundary: 0
        CompetencyResult(name="A", score=0, description="Reason")

        # Boundary: 100
        CompetencyResult(name="A", score=100, description="Reason")

        # Normal value
        CompetencyResult(name="A", score=85.5, description="Reason")

    def test_score_validation_too_low(self):
        """0 미만의 점수는 예외 발생"""
        with pytest.raises(ValidationError):
            CompetencyResult(name="A", score=-1, description="Reason")

    def test_score_validation_too_high(self):
        """100 초과의 점수는 예외 발생"""
        with pytest.raises(ValidationError):
            CompetencyResult(name="A", score=100.1, description="Reason")
