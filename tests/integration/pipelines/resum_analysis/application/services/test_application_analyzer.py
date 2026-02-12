import pytest
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# Import Service & Domain
from pipelines.resume_analysis.application.services.report import ApplicationAnalyzer

# Import Persistence (Real)
from pipelines.resume_analysis.infrastructure.persistence.job_repository import (
    SqlAlchemyJobRepository,
)
from pipelines.resume_analysis.infrastructure.persistence.doc_repository import (
    SqlAlchemyDocRepository,
)

# Import Adapters (Real & Mock)
from pipelines.resume_analysis.infrastructure.adapters.storage.s3_storage import (
    S3FileStorage,
)
from pipelines.resume_analysis.infrastructure.adapters.parser.pdf_extractor import (
    PyPdfExtractor,
)
from pipelines.resume_analysis.infrastructure.adapters.llm.mock_agent import (
    MockAnalyst,
)  # Mock Agent

# SQL Fixture Path
SQL_FILE_PATH = os.path.join(
    os.path.dirname(__file__), "../../../../../fixtures/data/test_data_insert.sql"
)


async def load_sql_file(session: AsyncSession, file_path: str):
    """SQL 파일 로드 Helper"""
    with open(file_path, "r", encoding="utf-8") as f:
        sql_content = f.read()
    statements = sql_content.split(";")
    for stmt in statements:
        if stmt.strip():
            await session.execute(text(stmt))


@pytest.mark.asyncio
async def test_analyze_resume_integration(db_session: AsyncSession):
    """
    [Integration Test] analyze_resume Service Logic
    - Job/Doc Repository: Real (DB)
    - Storage/Extractor: Real (S3/PDF) - *Requires S3 setup & actual file*
    - Agent: Mock (MockAnalyst)
    """
    # 1. 데이터 로드
    await load_sql_file(db_session, SQL_FILE_PATH)

    # 2. 의존성 주입
    job_repo = SqlAlchemyJobRepository(db_session)
    doc_repo = SqlAlchemyDocRepository(db_session)

    # 주의: S3FileStorage는 실제 AWS Credential과 S3 버킷/파일이 필요함.
    # 테스트 환경에 파일이 없다면 실패할 수 있음.
    # 여기서는 실제 구현체를 사용하되, 테스트 파일 경로(test_uploads/Resume.pdf)가 S3에 있다고 가정.
    file_storage = S3FileStorage()
    extractor = PyPdfExtractor()

    # Agent는 Mock 사용
    agent = MockAnalyst()

    service = ApplicationAnalyzer(
        job_repo=job_repo,
        doc_repo=doc_repo,
        file_storage=file_storage,  # Real Storage
        extractor=extractor,  # Real Extractor
        agent=agent,  # Mock Agent
    )

    # 3. 서비스 실행 (Resume)
    user_id = 991
    job_id = 9901

    try:
        response = await service.analyze_resume(user_id, job_id)

        # 4. 검증
        assert response is not None
        if hasattr(response, "ai_analysis_report"):  # Pydantic v2
            assert (
                "직무 적합도" in response.ai_analysis_report
                or "[Mock]" in response.ai_analysis_report
                or len(response.ai_analysis_report) > 0
            )

        # 상세항목 검증 (매퍼에 의해 section_analyses -> 각 필드로 변환됨)
        # job_fit_score 등이 채워졌는지 확인 (MockAnalyst는 모든 필드를 채워서 반환함)
        assert response.job_fit_score is not None
        assert response.experience_clarity_score is not None
        assert response.readability_score is not None

    except Exception as e:
        # S3 관련 에러면 스킵 (테스트 환경 문제)
        if "S3" in str(e) or "boto3" in str(e) or "No such file" in str(e):
            pytest.skip(f"Skipping test due to S3/File setup: {e}")
        else:
            raise e


@pytest.mark.asyncio
async def test_analyze_portfolio_integration(db_session: AsyncSession):
    """
    [Integration Test] analyze_portfolio Service Logic
    """
    # 1. 데이터 로드
    await load_sql_file(db_session, SQL_FILE_PATH)

    # 2. 서비스 생성
    service = ApplicationAnalyzer(
        job_repo=SqlAlchemyJobRepository(db_session),
        doc_repo=SqlAlchemyDocRepository(db_session),
        file_storage=S3FileStorage(),
        extractor=PyPdfExtractor(),
        agent=MockAnalyst(),
    )

    # 3. 서비스 실행 (Portfolio)
    user_id = 991
    job_id = 9901

    try:
        response = await service.analyze_portfolio(user_id, job_id)

        # 4. 검증
        assert response is not None
        if hasattr(response, "ai_analysis_report"):
            assert (
                "[Mock]" in response.ai_analysis_report
                or len(response.ai_analysis_report) > 0
            )

        # 상세항목 검증
        assert response.problem_solving_score is not None
        assert response.contribution_clarity_score is not None
        assert response.technical_depth_score is not None

    except Exception as e:
        if "S3" in str(e) or "boto3" in str(e) or "No such file" in str(e):
            pytest.skip(f"Skipping test due to S3/File setup: {e}")
        else:
            raise e
