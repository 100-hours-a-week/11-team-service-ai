
import pytest
import json
from unittest.mock import MagicMock, AsyncMock, patch
from pipelines.applicant_evaluation.infrastructure.adapters.llm.openai_agent import OpenAiAnalyst
from pipelines.applicant_evaluation.domain.models.job import JobInfo, EvaluationCriteria
from pipelines.applicant_evaluation.domain.models.evaluation import CompetencyResult
from pipelines.applicant_evaluation.domain.models.report import OverallFeedback
from shared.config import settings

# override_settings 제거됨 (OpenAiAnalyst는 더 이상 설정을 직접 참조하지 않음)

@pytest.fixture
def agent():
    # DI 덕분에 복잡한 patch 없이 Mock 객체 주입 가능!
    mock_client = MagicMock()
    # Async method mocking needed for client.chat.completions.create
    mock_client.chat.completions.create = AsyncMock()
    return OpenAiAnalyst(client=mock_client)

@pytest.fixture
def mock_job_info():
    return JobInfo(company_name="TestCo", main_tasks=[], tech_stacks=[], summary="Summary")

@pytest.mark.asyncio
async def test_evaluate_competency_success(agent, mock_job_info):
    """OpenAI 응답이 정상 JSON일 때 CompetencyResult 변환 성공"""
    # 1. Setup Mock Response
    mock_response_content = json.dumps({
        "score": 85.5,
        "reason": "Strong skills"
    })
    
    mock_completion = MagicMock()
    mock_completion.choices = [MagicMock(message=MagicMock(content=mock_response_content))]
    agent.client.chat.completions.create = AsyncMock(return_value=mock_completion)

    # 2. Execute
    criteria = EvaluationCriteria(name="Skill", description="Desc")
    result = await agent.evaluate_competency(mock_job_info, criteria, "Resume", "Portfolio")

    # 3. Verify
    assert isinstance(result, CompetencyResult)
    assert result.name == "Skill"
    assert result.score == 85.5
    assert result.description == "Strong skills"
    
    # Check if prompt was sent (basic check)
    agent.client.chat.completions.create.assert_awaited_once()

@pytest.mark.asyncio
async def test_synthesize_report_success(agent, mock_job_info):
    """OpenAI 응답이 정상 JSON일 때 OverallFeedback 변환 성공"""
    # 1. Setup Mock Response
    mock_response_content = json.dumps({
        "one_line_review": "Great!",
        "feedback_detail": "Detail..."
    })
    
    mock_completion = MagicMock()
    mock_completion.choices = [MagicMock(message=MagicMock(content=mock_response_content))]
    agent.client.chat.completions.create = AsyncMock(return_value=mock_completion)

    # 2. Execute
    comp_results = [CompetencyResult(name="Skill", score=90, description="Good")]
    result = await agent.synthesize_report(mock_job_info, comp_results)

    # 3. Verify
    assert isinstance(result, OverallFeedback)
    assert result.one_line_review == "Great!"
    assert result.feedback_detail == "Detail..."

@pytest.mark.asyncio
async def test_evaluate_competency_json_error(agent, mock_job_info):
    """OpenAI 응답이 JSON 형식이 아닐 때 JSONDecodeError 발생"""
    mock_response_content = "Not JSON String"
    
    mock_completion = MagicMock()
    mock_completion.choices = [MagicMock(message=MagicMock(content=mock_response_content))]
    agent.client.chat.completions.create = AsyncMock(return_value=mock_completion)

    criteria = EvaluationCriteria(name="Skill", description="Desc")
    
    with pytest.raises(json.JSONDecodeError):
        await agent.evaluate_competency(mock_job_info, criteria, "Resume", "")
