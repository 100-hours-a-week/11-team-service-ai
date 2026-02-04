from unittest.mock import patch

from fastapi.testclient import TestClient

from api.main import app
from shared.schema.job_posting import JobPostingAnalyzeResponse

client = TestClient(app)


def test_analyze_job_posting_success():
    # 1. Mock Data 준비
    mock_response_data = JobPostingAnalyzeResponse(
        job_posting_id=999,
        is_existing=False,
        company_name="Test Company",
        job_title="Test Job Title",
        main_responsibilities=["Code", "Test"],
        required_skills=["Python", "FastAPI"],
        recruitment_status="Open",
        recruitment_period=None,
        ai_summary="This is a test summary.",
    )

    # 2. Patch: 내부 Bridge 함수를 Mocking
    # Service 코드는 실제 실행되므로, Service가 Bridge를 잘 호출하는지도 검증됨
    with patch("api.service.job_posting.call_job_analysis") as mock_bridge_call:
        mock_bridge_call.return_value = mock_response_data

        # 3. 요청 실행
        payload = {"url": "http://example.com/job/123"}
        response = client.post("/ai/api/v1/job-posting/analyze", json=payload)

        # 4. 검증
        assert response.status_code == 200
        json_data = response.json()
        assert json_data["success"] is True
        assert json_data["data"]["company_name"] == "Test Company"
        assert json_data["data"]["job_posting_id"] == 999

        # Bridge 함수가 서비스에 의해 호출되었는지 확인
        mock_bridge_call.assert_called_once()

        # 호출 인자 검증 (Service가 Request 객체를 잘 만들어서 넘겼는지)
        args = mock_bridge_call.call_args[0]
        assert args[0].url == "http://example.com/job/123"


def test_analyze_job_posting_invalid_input():
    # URL 필드 누락
    payload = {}
    response = client.post("/ai/api/v1/job-posting/analyze", json=payload)

    # RequestValidationError 핸들러에 의해 400 Bad Request 반환 예상 (main.py 설정)
    assert response.status_code == 400
    json_data = response.json()
    assert json_data["success"] is False
    assert json_data["error"]["code"] == "INVALID_INPUT_VALUE"
