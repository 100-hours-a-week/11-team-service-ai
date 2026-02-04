import pytest
from pipelines.applicant_evaluation.domain.models.evaluation import CompetencyResult


class TestCompetencyResult:
    def test_score_validation_valid(self):
        """0 ~ 100 사이의 점수는 유효함"""
        # Boundary: 0
        c1 = CompetencyResult(name="A", score=0, description="Reason")
        c1.validate_score()

        # Boundary: 100
        c2 = CompetencyResult(name="A", score=100, description="Reason")
        c2.validate_score()

        # Normal value
        c3 = CompetencyResult(name="A", score=85.5, description="Reason")
        c3.validate_score()

    def test_score_validation_too_low(self):
        """0 미만의 점수는 예외 발생"""
        result = CompetencyResult(name="A", score=-1, description="Reason")
        with pytest.raises(ValueError, match="between 0 and 100"):
            result.validate_score()

    def test_score_validation_too_high(self):
        """100 초과의 점수는 예외 발생"""
        result = CompetencyResult(name="A", score=100.1, description="Reason")
        with pytest.raises(ValueError, match="between 0 and 100"):
            result.validate_score()
