
import pytest
from unittest.mock import AsyncMock, MagicMock
from pipelines.applicant_evaluation.application.services.analyzer import ApplicationAnalyzer
from pipelines.applicant_evaluation.domain.models.evaluation import CompetencyResult
from shared.schema.applicant import EvaluateResponse
from pipelines.applicant_evaluation.domain.models.report import OverallFeedback
from pipelines.applicant_evaluation.domain.models.job import JobInfo, EvaluationCriteria
from pipelines.applicant_evaluation.domain.models.document import ApplicantDocuments, ParsedDoc, FileInfo

@pytest.fixture
def mock_dependencies():
    return {
        "job_repo": AsyncMock(),
        "doc_repo": AsyncMock(),
        "file_storage": AsyncMock(),
        "extractor": AsyncMock(),
        "agent": AsyncMock(),
    }

@pytest.fixture
def analyzer(mock_dependencies):
    return ApplicationAnalyzer(**mock_dependencies)

@pytest.mark.asyncio
async def test_run_success_all_docs_ready(analyzer, mock_dependencies):
    """
    모든 문서가 이미 파싱된 상태(Real Objects)에서 정상적인 평가 흐름 테스트
    """
    # 1. Setup - Real Domain Objects
    job_id = 1
    user_id = 100
    
    # Real Job Object
    real_job = JobInfo(
        company_name="Test Company",
        main_tasks=["Python", "Cloud"],
        tech_stacks=["AWS", "Docker"],
        summary="A great job",
        evaluation_criteria=[
            EvaluationCriteria(name="직무적합성", description="Desc1"),
            EvaluationCriteria(name="성장가능성", description="Desc2")
        ]
    )
    mock_dependencies["job_repo"].get_job_info.return_value = real_job
    
    # Real Documents Object (Ready State)
    # 텍스트 길이를 50자 이상으로 해야 is_analyzable()이 True가 됨 (document.py 로직)
    valid_text = "A" * 60 
    real_docs = ApplicantDocuments(
        resume_file=FileInfo(file_path="s3://resume", file_type="RESUME"),
        parsed_resume=ParsedDoc(doc_type="RESUME", text=valid_text)
    )
    mock_dependencies["doc_repo"].get_documents.return_value = real_docs
    
    # Mock Agent Evaluation (Service Call)
    mock_result1 = CompetencyResult(name="직무적합성", score=80.0, description="Good")
    mock_result2 = CompetencyResult(name="성장가능성", score=90.0, description="Great")
    mock_dependencies["agent"].evaluate_competency.side_effect = [mock_result1, mock_result2]
    
    # Mock Synthesis
    mock_dependencies["agent"].synthesize_report.return_value = OverallFeedback(
        one_line_review="Excellent candidate",
        feedback_detail="Detailed feedback..."
    )

    # 2. Execute
    response = await analyzer.run(user_id, job_id)

    # 3. Verify
    assert isinstance(response, EvaluateResponse)
    assert response.overall_score == 85.0
    assert len(response.competency_scores) == 2
    
    # Verify Calls
    mock_dependencies["job_repo"].get_job_info.assert_awaited_once_with(job_id)
    mock_dependencies["doc_repo"].get_documents.assert_awaited_once_with(user_id, job_id)

@pytest.mark.asyncio
async def test_run_needs_document_processing(analyzer, mock_dependencies):
    """
    파싱된 문서가 없어서(Real Object Logic) 전처리가 실행되는 흐름 테스트
    """
    # 1. Setup
    job_id = 1
    user_id = 100
    
    real_job = JobInfo(
        company_name="Company", main_tasks=[], tech_stacks=[], summary="",
        evaluation_criteria=[EvaluationCriteria(name="기본", description="")]
    )
    mock_dependencies["job_repo"].get_job_info.return_value = real_job
    
    # State 1: Not Ready (파일은 있는데 파싱 데이터가 없음)
    docs_not_ready = ApplicantDocuments(
        resume_file=FileInfo(file_path="s3://resume.pdf", file_type="RESUME"),
        parsed_resume=None # Missing
    )
    
    # State 2: Ready (파싱 후 상태)
    valid_text = "A" * 60
    docs_ready = ApplicantDocuments(
        resume_file=FileInfo(file_path="s3://resume.pdf", file_type="RESUME"),
        parsed_resume=ParsedDoc(doc_type="RESUME", text=valid_text)
    )
    
    # Repository returns: First -> Not Ready, Second -> Ready
    mock_dependencies["doc_repo"].get_documents.side_effect = [docs_not_ready, docs_ready]
    
    # Mock Extraction Flow
    mock_dependencies["file_storage"].download_file.return_value = b"PDF_BYTES"
    mock_dependencies["extractor"].extract_text.return_value = valid_text
    
    # Mock Agent
    mock_dependencies["agent"].evaluate_competency.return_value = CompetencyResult(name="기본", score=50, description="Normal")
    mock_dependencies["agent"].synthesize_report.return_value = OverallFeedback(one_line_review="TBD", feedback_detail="TBD")

    # 2. Execute
    await analyzer.run(user_id, job_id)

    # 3. Verify Extraction Flow
    # 실제 ApplicantDocuments.get_missing_parsed_types() 로직에 의해 RESUME이 감지되었는지 확인
    # 따라서 download_file이 호출되었어야 함
    mock_dependencies["file_storage"].download_file.assert_awaited_with("s3://resume.pdf") 
    mock_dependencies["extractor"].extract_text.assert_awaited_with(b"PDF_BYTES")
    mock_dependencies["doc_repo"].save_parsed_doc.assert_awaited_once()

@pytest.mark.asyncio
async def test_run_job_not_found(analyzer, mock_dependencies):
    """
    Job 정보가 없을 때 예외 발생 테스트
    """
    mock_dependencies["job_repo"].get_job_info.return_value = None
    
    with pytest.raises(ValueError, match="Job not found"):
        await analyzer.run(user_id=1, job_id=999)
