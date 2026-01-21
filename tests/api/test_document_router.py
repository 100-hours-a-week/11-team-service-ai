from unittest.mock import patch

from fastapi.testclient import TestClient

from api.main import app
from shared.schema.document import PortfolioAnalyzeResponse, ResumeAnalyzeResponse

client = TestClient(app)


def test_analyze_resume_success():
    # 1. Mock Data
    mock_response = ResumeAnalyzeResponse(
        ai_analysis_report="Great resume",
        job_fit_score="Perfect",
        experience_clarity_score="Clear",
        readability_score="Good",
    )
    
    # 2. Patch: api.service.document.call_resume_analysis
    with patch("api.service.document.call_resume_analysis") as mock_call:
        mock_call.return_value = mock_response

        payload = {"user_id": "u1", "job_posting_id": "j1"}
        response = client.post("/api/v1/resume/analyze", json=payload)

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["success"] is True
        assert json_data["data"]["job_fit_score"] == "Perfect"
        mock_call.assert_called_once()


def test_analyze_portfolio_success():
    # 1. Mock Data
    mock_response = PortfolioAnalyzeResponse(
        ai_analysis_report="Great portfolio",
        problem_solving_score="Excellent",
        contribution_clarity_score="Clear",
        technical_depth_score="Deep",
    )

    # 2. Patch
    with patch("api.service.document.call_portfolio_analysis") as mock_call:
        mock_call.return_value = mock_response

        payload = {"user_id": "u1", "job_posting_id": "j1"}
        response = client.post("/api/v1/portfolio/analyze", json=payload)

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["success"] is True
        assert json_data["data"]["problem_solving_score"] == "Excellent"
        mock_call.assert_called_once()
