from unittest.mock import patch

from fastapi.testclient import TestClient

from api.main import app
from shared.schema.applicant import (
    CompareResponse,
    ComparisonMetric,
    CompetencyScore,
    EvaluateResponse,
)

client = TestClient(app)


def test_evaluate_applicant_success():
    # 1. Mock Data
    mock_response = EvaluateResponse(
        overall_score=88.5,
        competency_scores=[
            CompetencyScore(name="Skill", score=90, description="Great"),
            CompetencyScore(name="Exp", score=80, description="Good"),
        ],
        one_line_review="Excellent candidate",
        feedback_detail="Detail feedback",
    )

    # 2. Patch
    with patch("api.service.applicant.call_applicant_evaluation") as mock_call:
        mock_call.return_value = mock_response

        # 3. Request
        payload = {"user_id": "user_123", "job_posting_id": "job_456"}
        response = client.post("/ai/api/v1/applicant/evaluate", json=payload)

        # 4. Verify
        assert response.status_code == 200
        json_data = response.json()
        assert json_data["success"] is True
        assert json_data["data"]["overall_score"] == 88.5
        assert len(json_data["data"]["competency_scores"]) == 2
        mock_call.assert_called_once()


def test_compare_applicants_success():
    # 1. Mock Data
    mock_response = CompareResponse(
        comparison_metrics=[
            ComparisonMetric(name="Skill", my_score=80, competitor_score=70),
        ],
        strengths_report="Better skills",
        weaknesses_report="Less exp",
    )

    # 2. Patch
    with patch("api.service.applicant.call_candidate_comparison") as mock_call:
        mock_call.return_value = mock_response

        # 3. Request
        payload = {
            "user_id": "me",
            "job_posting_id": "job_1",
            "competitor": "other_guy",
        }
        response = client.post("/ai/api/v1/applicant/compare", json=payload)

        # 4. Verify
        assert response.status_code == 200
        json_data = response.json()
        assert json_data["success"] is True
        assert json_data["data"]["strengths_report"] == "Better skills"
        assert json_data["data"]["comparison_metrics"][0]["name"] == "Skill"
        mock_call.assert_called_once()
