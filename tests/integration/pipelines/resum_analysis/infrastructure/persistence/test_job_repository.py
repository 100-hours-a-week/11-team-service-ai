import pytest
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# Import Repository
from pipelines.resume_analysis.infrastructure.persistence.job_repository import SqlAlchemyJobRepository
from pipelines.resume_analysis.domain.models.job import JobInfo

# SQL 파일 경로
SQL_FILE_PATH = os.path.join(
    os.path.dirname(__file__), 
    "../../../../../fixtures/data/test_data_insert.sql"
)

async def load_sql_file(session: AsyncSession, file_path: str):
    """
    SQL 파일을 읽어 세션에서 실행
    """
    with open(file_path, "r", encoding="utf-8") as f:
        sql_content = f.read()
        
    # SQL 문이 여러 개일 수 있으므로 ;로 분리하여 실행 (간단한 파싱)
    statements = sql_content.split(";")
    for stmt in statements:
        if stmt.strip():
            await session.execute(text(stmt))

@pytest.mark.asyncio
async def test_get_job_info_integration(db_session: AsyncSession):
    """
    [Integration Test] JobRepository.get_job_info
    - Fixture 데이터를 DB에 삽입수, Repository를 통해 조회되는지 검증
    """
    # 1. 테스트 데이터 삽입 (Fixture)
    # 주의: conftest.py의 db_session은 트랜잭션을 롤백하므로, 
    # 데이터 삽입도 동일한 세션 내에서 수행해야 조회 가능함.
    try:
        await load_sql_file(db_session, SQL_FILE_PATH)
    except Exception as e:
        pytest.fail(f"Failed to load SQL fixture: {e}")

    # 2. Repository 초기화
    repo = SqlAlchemyJobRepository(db_session)
    job_id = 9901  # test_data_insert.sql에 정의된 Job ID

    # 3. 메서드 실행
    job_info = await repo.get_job_info(job_id)

    # 4. 검증 (Assertion)
    assert job_info is not None, "JobInfo should not be None"
    assert isinstance(job_info, JobInfo)
    
    # 데이터 검증 (test_data_insert.sql 내용 기반)
    # 회사명: TechCorp Inc. (ID: 991)
    assert job_info.company_name == "TechCorp Inc."
    
    # 기술 스택: Java, Spring Boot, MySQL, Docker (ID: 9901~9904)
    expected_stacks = {"[Java]", "[Spring Boot]", "[MySQL]", "[Docker]"}
    assert set(job_info.tech_stacks) == expected_stacks
    
    # 평가 기준 검증 (JSON 파싱 확인)
    assert len(job_info.evaluation_criteria) == 4
    assert job_info.evaluation_criteria[0].name == "직무 적합성"
    
    # 요약 정보 확인
    assert "백엔드 엔지니어" in job_info.summary or "Java" in job_info.summary

