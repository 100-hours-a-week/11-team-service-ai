
import asyncio
import logging
from job_analysis.normalizer.company_normalizer import CompanyNormalizer
from shared.db.connection import get_db
from job_analysis.data.repository.company_repository import CompanyRepository

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    logger.info("🚀 Starting CompanyNormalizer manual test...")

    # Real DB Injection
    async for session in get_db():
        try:
            logger.info("✅ DB Session connected.")
            company_repo = CompanyRepository(session)
            
            # Initialize Normalizer with Real Repo
            normalizer = CompanyNormalizer(repo=company_repo)
            
            # 1. "네이버" db, vector db초기화 후 naver로 처음 실행
            # 2. db, vector db에 naver확인
            # 3. 네이버로 실행 company_alias에 네이버 추가된것 확인
            test_company_name = "(주)네이버" 
            
            logger.info(f"🧪 Testing get_or_create for: {test_company_name}")
            
            try:
                # Full Flow Test (Find -> Match or Create -> Vector DB)
                company_id = await normalizer.get_or_create(test_company_name)
                
                logger.info(f"🎉 Result Company ID: {company_id}")
                
                # Verify commit if needed (get_or_create usually relies on repo.create which might flush, 
                # but session.commit() is needed to persist to DB permanently if repo doesn't auto-commit)
                await session.commit() 
                
            except Exception as e:
                logger.error(f"❌ Error during test: {e}")
                await session.rollback()
                
        finally:
            # Session closed by async generator, but good practice to ensure clean
            pass
        break # get_db is a generator, we just need one session

if __name__ == "__main__":
    asyncio.run(main())
