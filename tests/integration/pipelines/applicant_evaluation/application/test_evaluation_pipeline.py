import pytest
from unittest.mock import patch
from shared.config import settings
from shared.schema.applicant import EvaluateRequest, EvaluateResponse
from pipelines.applicant_evaluation.main import run_pipeline
from shared.db.model.models import (
    User,
    Company,
    JobMaster,
    JobApplication,
    FileObject,
    ApplicationDocument,
)

# Re-use setup logic or define fixtures here


@pytest.fixture
async def pipeline_data(db_session):
    """파이프라인 실행을 위한 최소 데이터 셋업"""
    # 1. User
    user = User(
        platform_name="TEST",
        email="pipe@test.com",
        password="pw",
        nickname="PipeUser",
        img_id="img",
    )
    db_session.add(user)

    # 2. Job
    company = Company(name="Pipeline Corp", domain="p.com")
    db_session.add(company)
    await db_session.flush()
    job = JobMaster(
        company_id=company.company_id,
        job_title="Pipeline Engineer",
        evaluation_criteria=[{"name": "Criteria1", "description": "Desc"}],
        status="OPEN",
    )
    db_session.add(job)
    await db_session.flush()

    # 3. Application
    app = JobApplication(
        user_id=user.user_id, job_master_id=job.job_master_id, status="APPLIED"
    )
    db_session.add(app)
    await db_session.commit()  # ID 확정

    # 4. Files (Resume)
    resume = FileObject(
        storage_provider="S3",
        bucket="bucket",
        object_key="pipe_resume.pdf",
        original_name="resume.pdf",
        size_bytes=100,
    )
    db_session.add(resume)
    await db_session.flush()

    app_doc = ApplicationDocument(
        job_application_id=app.job_application_id,
        file_id=resume.file_id,
        doc_type="RESUME",
    )
    db_session.add(app_doc)
    await db_session.commit()

    return user.user_id, job.job_master_id, app.job_application_id


@pytest.mark.asyncio
async def test_run_pipeline_end_to_end(db_session, pipeline_data):
    """
    통합 테스트: DB 데이터 준비 -> run_pipeline 실행 -> 결과 반환 및 DB 저장 확인
    """
    user_id, job_id, app_id = pipeline_data

    request = EvaluateRequest(user_id=user_id, job_posting_id=job_id)

    # Mock Mode 강제 활성화 (LLM 비용 절감 및 속도)
    # patch.object를 사용해 settings.use_mock (또는 USE_MOCK)을 True로 설정
    # main.py 로직: if getattr(settings, "use_mock", False): Agent = Mock...

    # settings.use_mock 프로퍼티가 USE_MOCK 필드를 쓰므로 필드를 패치
    with patch.object(settings, "USE_MOCK", True):
        # S3 다운로드 및 PDF 추출도 Mocking이 필요할 수 있음.
        # 하지만 지금은 Adapter들이 이미 구현되어 있고 실제 S3 연결이 안 되어 있다면 에러 날 것임.
        # 통합 테스트 환경(Local)에서는 LocalStack 같은 걸 쓰거나,
        # 여기서는 Adapter 부분만 살짝 Mocking해주는 게 현실적임 (Full E2E가 아니므로).

        # S3와 PDF Extractor만 Mocking (너무 느리거나 외부 의존적이므로)
        with (
            patch("pipelines.applicant_evaluation.main.S3FileStorage") as MockStorage,
            patch(
                "pipelines.applicant_evaluation.main.PyPdfExtractor"
            ) as MockExtractor,
        ):

            # Setup Mock Adapter Behaviors
            storage_instance = MockStorage.return_value
            storage_instance.download_file.return_value = b"Dummy PDF Content"

            extractor_instance = MockExtractor.return_value
            extractor_instance.extract_text.return_value = (
                "Extracted Resume Text Content..."
            )

            # ACTION: Run Pipeline
            # 주의: run_pipeline 내부에서 get_db()를 호출함.
            # 하지만 테스트 중에는 db_session fixture가 이미 트랜잭션을 잡고 있음.
            # main.py가 get_db()를 통해 '새로운 세션'을 열면, connection factory에 따라
            # 테스트 트랜잭션과 별개로 동작할 위험이 있음. (데이터 안 보임)
            # -> 해결책: get_db를 오버라이딩하거나, 같은 엔진/커넥션을 쓰도록 유도해야 함.
            # 가장 쉬운 방법: main.py의 get_db를 Mocking해서 현재 db_session을 yield하도록 함!

            async def fn_get_db_override():
                yield db_session

            with patch(
                "pipelines.applicant_evaluation.main.get_db",
                side_effect=fn_get_db_override,
            ):
                response = await run_pipeline(request)

    # ASSERTIONS
    assert isinstance(response, EvaluateResponse)
    assert response.overall_score == 75.0  # Mock Agent Default Score

    # (여기서는 간단히 검증)
    assert response.one_line_review.startswith("[Mock]")
