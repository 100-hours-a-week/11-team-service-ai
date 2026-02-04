import pytest
from shared.db.model.models import (
    User,
    Company,
    JobMaster,
    JobApplication,
    ApplicationDocument,
    FileObject,
    ApplicationDocumentParsed,
)
from pipelines.applicant_evaluation.infrastructure.persistence.doc_repository import (
    SqlAlchemyDocRepository,
)
from pipelines.applicant_evaluation.domain.models.document import (
    ApplicantDocuments,
    ParsedDoc,
)


@pytest.fixture
async def setup_base_data(db_session):
    """
    기본 데이터 생성 Fixture: User, Company, JobMaster, JobApplication
    """
    # 1. User
    user = User(
        platform_name="KAKAO",
        email="test@kakao.com",
        password="pw",
        nickname="Tester",
        img_id="img",
    )
    db_session.add(user)

    # 2. Company & Job
    company = Company(name="DocTest Corp", domain="doctest.com")
    db_session.add(company)
    await db_session.flush()

    job = JobMaster(company_id=company.company_id, job_title="Engineer", status="OPEN")
    db_session.add(job)
    await db_session.flush()

    # 3. Application (지원)
    application = JobApplication(
        user_id=user.user_id, job_master_id=job.job_master_id, status="APPLIED"
    )
    db_session.add(application)
    await db_session.commit()

    return user, job, application


@pytest.mark.asyncio
async def test_get_documents_with_files(db_session, setup_base_data):
    """파일 정보가 있을 때 ApplicantDocuments로 잘 조회되는지 테스트"""
    user, job, app = setup_base_data
    repo = SqlAlchemyDocRepository(db_session)

    # 1. 파일 정보 추가 (RESUME)
    resume_file = FileObject(
        storage_provider="S3",
        bucket="bucket",
        object_key="resume.pdf",
        original_name="resume.pdf",
        size_bytes=100,
    )
    db_session.add(resume_file)
    await db_session.flush()

    app_doc = ApplicationDocument(
        job_application_id=app.job_application_id,
        file_id=resume_file.file_id,
        doc_type="RESUME",
    )
    db_session.add(app_doc)
    await db_session.commit()

    # 2. 조회 실행
    docs = await repo.get_documents(user.user_id, job.job_master_id)

    # 3. 검증
    assert isinstance(docs, ApplicantDocuments)
    assert docs.resume_file is not None
    assert (
        docs.resume_file.file_path == "resume.pdf"
    )  # 저장된 key 확인 (Repo 로직에 따라 다를 수 있음)
    assert docs.portfolio_file is None  # 포트폴리오는 안 넣었으므로
    assert docs.parsed_resume is None  # 파싱 데이터도 안 넣음


@pytest.mark.asyncio
async def test_get_documents_with_parsed(db_session, setup_base_data):
    """파싱된 데이터까지 있을 때 조회 테스트"""
    user, job, app = setup_base_data
    repo = SqlAlchemyDocRepository(db_session)

    # 1. 파일 & 파싱 데이터 추가 (PORTFOLIO)
    pf_file = FileObject(
        storage_provider="S3",
        bucket="bucket",
        object_key="pf.pdf",
        original_name="pf.pdf",
        size_bytes=200,
    )
    db_session.add(pf_file)
    await db_session.flush()

    app_doc = ApplicationDocument(
        job_application_id=app.job_application_id,
        file_id=pf_file.file_id,
        doc_type="PORTFOLIO",
    )
    db_session.add(app_doc)
    await db_session.flush()

    parsed = ApplicationDocumentParsed(
        application_document_id=app_doc.application_document_id,
        raw_text="Parsed Portfolio Content",
        parsing_status="SUCCESS",
    )
    db_session.add(parsed)
    await db_session.commit()

    # 2. 조회
    docs = await repo.get_documents(user.user_id, job.job_master_id)

    # 3. 검증
    assert docs.portfolio_file is not None
    assert docs.parsed_portfolio is not None
    assert docs.parsed_portfolio.text == "Parsed Portfolio Content"


@pytest.mark.asyncio
async def test_save_parsed_doc(db_session, setup_base_data):
    """파싱 결과를 저장하는 기능 테스트"""
    user, job, app = setup_base_data
    repo = SqlAlchemyDocRepository(db_session)

    # 1. 파일 정보만 존재 (RESUME)
    resume_file = FileObject(
        storage_provider="S3",
        bucket="bucket",
        object_key="r.pdf",
        original_name="r.pdf",
        size_bytes=100,
    )
    db_session.add(resume_file)
    await db_session.flush()

    app_doc = ApplicationDocument(
        job_application_id=app.job_application_id,
        file_id=resume_file.file_id,
        doc_type="RESUME",
    )
    db_session.add(app_doc)
    await db_session.commit()

    # 2. 저장 실행
    # 주의: save_parsed_doc 인자가 (user_id, job_id, doc_type, ParsedDoc) 인지 확인 필요
    # 보통 Repository는 Entity Id 기반보다는 Domain Key 기반으로 설계하는 경우가 많음.
    # 여기서는 Repo 구현에 따름(지금은 user_id, job_id 기반으로 가정)

    new_parsed = ParsedDoc(doc_type="RESUME", text="New Extracted Text")
    await repo.save_parsed_doc(user.user_id, job.job_master_id, new_parsed)

    # 3. DB 직접 확인 (검증)
    # 저장된 데이터가 ApplicationDocumentParsed에 있는지 쿼리
    # (세션이 다를 수 있으므로 commit/refresh 유의. 여기선 같은 세션)

    # application_document_parsed와 application_document 조인 조회
    assert app_doc.parsed is not None
    # 관계 로딩이 안 되어 있을 수 있으므로 Refresh
    await db_session.refresh(app_doc, ["parsed"])

    # application_document.parsed는 List일 수 있음 (1:N or 1:1)
    # 모델 정의상: parsed: Mapped[List["ApplicationDocumentParsed"]]
    assert len(app_doc.parsed) > 0
    saved_content = app_doc.parsed[0]
    assert saved_content.raw_text == "New Extracted Text"
