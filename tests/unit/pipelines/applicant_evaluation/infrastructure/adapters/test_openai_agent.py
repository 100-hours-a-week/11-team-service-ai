import pytest
import json

from pipelines.applicant_evaluation.infrastructure.adapters.llm.ai_agent import (
    LLMAnalyst,
)
from pipelines.applicant_evaluation.domain.models.job import JobInfo, EvaluationCriteria
from pipelines.applicant_evaluation.domain.models.evaluation import CompetencyResult
from pipelines.applicant_evaluation.domain.models.report import OverallFeedback

# override_settings 제거됨 (LLMAnalyst는 더 이상 설정을 직접 참조하지 않음)


from langchain_core.language_models import FakeListChatModel


@pytest.fixture
def agent():
    # Use FakeListChatModel to simulate LLM responses cleanly through LCEL
    # We will populate the responses in each test case
    fake_llm = FakeListChatModel(responses=[])
    return LLMAnalyst(llm=fake_llm)


@pytest.fixture
def mock_job_info():
    return JobInfo(
        company_name="TestCo",
        main_tasks=[],
        tech_stacks=[],
        summary="Summary",
        evaluation_criteria=[EvaluationCriteria(name="Criteria1", description="desc")],
    )


@pytest.mark.asyncio
async def test_evaluate_competency_success(agent, mock_job_info):
    """LLM 응답이 정상일 때 CompetencyResult 반환 성공"""
    # 1. Setup Mock Response
    response_json = json.dumps(
        {"name": "Skill", "score": 85.5, "description": "Strong skills"}
    )
    agent.llm.responses = [response_json]

    # 2. Execute
    criteria = EvaluationCriteria(name="Skill", description="Desc")
    result = await agent.evaluate_competency(
        mock_job_info, criteria, "Resume", "Portfolio"
    )

    # 3. Verify
    assert isinstance(result, CompetencyResult)
    # Note: Name is set from criteria name inside the method, score/desc from LLM
    assert result.name == "Skill"
    assert result.score == 85.5
    assert result.description == "Strong skills"


@pytest.mark.asyncio
async def test_synthesize_report_success(agent, mock_job_info):
    """LLM 응답이 정상일 때 OverallFeedback 변환 성공"""
    # 1. Setup Mock Response
    response_json = json.dumps(
        {"one_line_review": "Great!", "feedback_detail": "Detail..."}
    )
    agent.llm.responses = [response_json]

    # 2. Execute
    comp_results = [CompetencyResult(name="Skill", score=90, description="Good")]
    result = await agent.synthesize_report(mock_job_info, comp_results)

    # 3. Verify
    assert isinstance(result, OverallFeedback)
    assert result.one_line_review == "Great!"
    assert result.feedback_detail == "Detail..."


@pytest.mark.asyncio
async def test_evaluate_competency_json_error(agent, mock_job_info):
    """LLM 응답이 JSON 파싱 실패시 0점 처리"""
    # 1. Setup Mock Response with Invalid JSON
    agent.llm.responses = ["Not JSON String"]

    # 2. Execute
    criteria = EvaluationCriteria(name="Skill", description="Desc")
    result = await agent.evaluate_competency(mock_job_info, criteria, "Resume", "")

    # 3. Verify - Exception caught and error result returned
    assert result.score == 0.0
    assert "Evaluation Error" in result.description
    # assert result.name == "Skill" (Optional check)
