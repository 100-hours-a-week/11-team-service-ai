import pytest
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# Import Repository
from pipelines.resume_analysis.infrastructure.persistence.doc_repository import (
    SqlAlchemyDocRepository,
)
from pipelines.resume_analysis.domain.models.document import DocumentType

# SQL 파일 경로 (같은 fixture 사용)
SQL_FILE_PATH = os.path.join(
    os.path.dirname(__file__), "../../../../../fixtures/data/test_data_insert.sql"
)


async def load_sql_file(session: AsyncSession, file_path: str):
    """
    SQL 파일을 읽어 세션에서 실행 (동일한 헬퍼)
    """
    with open(file_path, "r", encoding="utf-8") as f:
        sql_content = f.read()

    statements = sql_content.split(";")
    for stmt in statements:
        if stmt.strip():
            await session.execute(text(stmt))


@pytest.mark.asyncio
async def test_get_document_integration(db_session: AsyncSession):
    """
    [Integration Test] DocRepository.get_document
    - 이력서 및 포트폴리오 문서 정보 및 파싱된 텍스트 조회 검증
    """
    # 1. 데이터 로드
    await load_sql_file(db_session, SQL_FILE_PATH)

    repo = SqlAlchemyDocRepository(db_session)
    user_id = 991
    job_id_resume = 9901  # Resume가 연결된 공고
    job_id_portfolio = 9901  # Portfolio가 연결된 공고 (test_data_insert.sql 참고)

    # 2. 이력서 조회
    resume_doc = await repo.get_document(user_id, job_id_resume, DocumentType.RESUME)

    assert resume_doc is not None
    assert resume_doc.doc_type == DocumentType.RESUME
    assert resume_doc.file_path == "test_uploads/Resume.pdf"
    # test_data_insert.sql에는 파싱된 텍스트가 없으므로 None이어야 함 (또는 초기값)
    assert resume_doc.extracted_text is None

    # 3. 포트폴리오 조회
    portfolio_doc = await repo.get_document(
        user_id, job_id_portfolio, DocumentType.PORTFOLIO
    )

    assert portfolio_doc is not None
    assert portfolio_doc.doc_type == DocumentType.PORTFOLIO
    assert portfolio_doc.file_path == "test_uploads/Portfolio.pdf"


@pytest.mark.asyncio
async def test_save_parsed_doc_integration(db_session: AsyncSession):
    """
    [Integration Test] DocRepository.save_parsed_doc
    - 파싱된 텍스트 저장 및 업데이트 검증
    """
    # 1. 데이터 로드
    await load_sql_file(db_session, SQL_FILE_PATH)

    repo = SqlAlchemyDocRepository(db_session)
    user_id = 991
    job_id = 9901
    doc_type = DocumentType.RESUME

    # 2. 초기 상태 확인 (위 테스트와 중복되지만 독립 실행 보장)
    doc = await repo.get_document(user_id, job_id, doc_type)
    assert doc is not None
    assert doc.extracted_text is None

    # 3. 텍스트 업데이트 및 저장
    new_text = "This is a parsed resume text."
    doc.update_text(new_text)

    await repo.save_parsed_doc(user_id, job_id, doc)

    # 4. 다시 조회하여 저장 확인
    # 같은 세션 내에서는 캐시될 수 있으므로, 확실한 검증을 위해 refresh하거나
    # Repository 로직이 DB에 write하는지 확인 (현재 로직은 merge/add)
    # 여기서는 같은 세션에서 조회

    updated_doc = await repo.get_document(user_id, job_id, doc_type)
    assert updated_doc is not None
    assert updated_doc.extracted_text == new_text
