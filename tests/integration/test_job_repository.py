import pytest
import sys
import os
import asyncio

# 프로젝트 루트 경로 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from shared.db.connection import get_db
from pipelines.applicant_evaluation.infrastructure.persistence.job_repository import SqlAlchemyJobRepository
from sqlalchemy import text

@pytest.mark.asyncio
async def test_job_repository_retrieval():
    """
    SqlAlchemyJobRepository가 실제 DB(job_master_id=9901)에서 
    정보를 올바르게 조회하고 JobInfo 도메인 객체로 변환하는지 테스트
    """
    print("\n🚀 Starting Job Repository Integration Test...")

    # DB 세션을 비동기 제너레이터(get_db)로부터 가져옴
    async for session in get_db():
        try:
            # 0. 사전 데이터 확인 (Optional: 데이터가 있는지 간단 체크)
            try:
                result = await session.execute(text("SELECT count(*) FROM job_masters WHERE job_master_id = 9901"))
                count = result.scalar()
                if count == 0:
                    pytest.skip("⚠️ Test data (ID: 9901) not found. Please run 'tests/test_data_insert.sql' first.")
            except Exception as e:
                print(f"⚠️ Warning during pre-check: {e}")

            # 1. Repository 초기화
            repo = SqlAlchemyJobRepository(session)
            target_job_id = 9901

            # 2. get_job_info 실행 (Async 메서드 호출)
            print(f"🔍 Querying Job Info for ID: {target_job_id}")
            job_info = await repo.get_job_info(target_job_id)

            # 3. 검증 (Assertions)
            assert job_info is not None, "JobInfo should not be None"
            
            print("\n✅ Job Info Retrieved Successfully!")
            print(f"   🏢 Company: {job_info.company_name}")
            print(f"   📝 Summary: {job_info.summary}")
            print(f"   🛠️ Tech Stacks: {job_info.tech_stacks}")
            print(f"   📋 Main Tasks: {job_info.main_tasks}")
            print(f"   ⚖️ Criteria Count: {len(job_info.evaluation_criteria)}")
            for idx, c in enumerate(job_info.evaluation_criteria, 1):
                print(f"      {idx}. {c.name}: {c.description[:50]}...")

            # 상세 검증
            assert job_info.company_name == "TechCorp Inc."
            assert "Backend Engineer" in job_info.summary or "백엔드 개발자" in job_info.summary or "엔지니어" in job_info.summary
            
            # Tech Stacks 확인
            expected_stacks = {"Java", "Spring Boot", "MySQL", "Docker"}
            retrieved_stacks = set(job_info.tech_stacks)
            assert expected_stacks.issubset(retrieved_stacks), f"Missing stacks. Expected subset: {expected_stacks}, Got: {retrieved_stacks}"

            # Main Tasks (JSON Parsing) 확인
            assert len(job_info.main_tasks) == 3
            assert "RESTful API" in job_info.main_tasks[0] or "설계" in job_info.main_tasks[0]

            # Evaluation Criteria 확인
            assert len(job_info.evaluation_criteria) == 4
            criteria_names = [c.name for c in job_info.evaluation_criteria]
            assert "직무 적합성" in criteria_names
            assert "조직 융화력" in criteria_names

        except Exception as e:
            pytest.fail(f"❌ Job Repository Test Failed: {e}")

if __name__ == "__main__":
    # 비동기 테스트 실행을 위한 헬퍼
    asyncio.run(test_job_repository_retrieval())
