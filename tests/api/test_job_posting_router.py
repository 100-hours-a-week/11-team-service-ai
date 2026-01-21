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

    # 2. Patch: api.service.job_posting 모듈에서 사용하는 call_job_analysis 함수를 Mocking
    # 주의: patch 위치는 '정의된 곳'이 아니라 '사용되는 곳'이어야 합니다.
    with patch("api.service.job_posting.call_job_analysis") as mock_call:
        mock_call.return_value = mock_response_data

        # 3. 요청 실행
        payload = {"url": "http://example.com/job/123"}
        response = client.post("/api/v1/job-posting/analyze", json=payload)

        # 4. 검증
        assert response.status_code == 200
        json_data = response.json()
        assert json_data["success"] is True
        assert json_data["data"]["company_name"] == "Test Company"
        assert json_data["data"]["job_posting_id"] == 999

        # Mock 함수가 한 번 호출되었는지 확인
        mock_call.assert_called_once()
        # 전달된 인자 확인 (선택 사항)
        called_arg = mock_call.call_args[0][0]
        assert called_arg.url == "http://example.com/job/123"


def test_analyze_job_posting_invalid_input():
    # URL 필드 누락
    payload = {}
    response = client.post("/api/v1/job-posting/analyze", json=payload)

    # RequestValidationError 핸들러에 의해 400 Bad Request 반환 예상 (main.py 설정)
    assert response.status_code == 400
    json_data = response.json()
    assert json_data["success"] is False
    assert json_data["error"]["code"] == "INVALID_INPUT_VALUE"
