import pytest
import sys
import os
import asyncio

# 프로젝트 루트 경로 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from shared.db.connection import get_db
from pipelines.applicant_evaluation.infrastructure.persistence.doc_repository import SqlAlchemyDocRepository
from sqlalchemy import text

@pytest.mark.asyncio
async def test_doc_repository_retrieval():
    """
    SqlAlchemyDocRepository가 실제 DB(user_id=991, job_master_id=9901)에서 
    이력서/포트폴리오 문서 정보를 올바르게 조회하고 ApplicantDocuments 도메인 객체로 변환하는지 테스트
    """
    print("\n🚀 Starting Document Repository Integration Test...")

    async for session in get_db():
        try:
            # 0. 사전 데이터 체크
            try:
                result = await session.execute(text(
                    "SELECT count(*) FROM job_applications WHERE user_id=991 AND job_master_id=9901"
                ))
                count = result.scalar()
                if count == 0:
                    pytest.skip("⚠️ Test data not found. Please run 'tests/test_data_insert.sql'.")
            except Exception as e:
                print(f"⚠️ Warning during pre-check: {e}")

            # 1. Repository 초기화
            repo = SqlAlchemyDocRepository(session)
            
            user_id = 991
            job_id = 9901

            # 2. get_documents 실행
            print(f"🔍 Querying Documents (User: {user_id}, Job: {job_id})")
            docs = await repo.get_documents(user_id, job_id)

            # 3. 검증
            print("\n✅ Document Info Retrieved Successfully!")
            
            # --- Resume 검증 ---
            resume = docs.resume_file
            parsed_resume = docs.parsed_resume
            
            if resume:
                print(f"   📄 Resume Found: Path='{resume.file_path}', Type='{resume.file_type}'")
                assert resume.file_type == "RESUME", "Resume file type mismatch"
            else:
                pytest.fail("❌ Resume file info missing")

            if parsed_resume:
                print(f"      Parsed Text: {parsed_resume.text[:50]}...")
                assert "Backend Developer" in parsed_resume.text or "Java" in parsed_resume.text, "Resume text mismatch"
            else:
                print("      ⚠️ Parsed resume data missing")

            # --- Portfolio 검증 ---
            portfolio = docs.portfolio_file
            parsed_portfolio = docs.parsed_portfolio
            
            if portfolio:
                print(f"   🎨 Portfolio Found: Path='{portfolio.file_path}', Type='{portfolio.file_type}'")
                assert portfolio.file_type == "PORTFOLIO", "Portfolio file type mismatch"
            else:
                pytest.fail("❌ Portfolio file info missing")
                
            if parsed_portfolio:
                print(f"      Parsed Text: {parsed_portfolio.text[:50]}...")
                assert "Project" in parsed_portfolio.text or "Microservices" in parsed_portfolio.text, "Portfolio text mismatch"
            else:
                print("      ⚠️ Parsed portfolio data missing")

        except Exception as e:
            pytest.fail(f"❌ Doc Repository Test Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_doc_repository_retrieval())
