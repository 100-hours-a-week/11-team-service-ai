
import asyncio
import logging
from job_analysis.normalizer.skill_normalizer import SkillNormalizer

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from shared.db.connection import get_db
from job_analysis.data.repository.skill_repository import SkillRepository

async def main():
    logger.info("🚀 Starting SkillNormalizer manual test...")

    # Real DB Injection
    async for session in get_db():
        try:
            logger.info("✅ DB Session connected.")
            skill_repo = SkillRepository(session)
            
            # Initialize Normalizer with Real Repo
            normalizer = SkillNormalizer(repo=skill_repo)
            
            # 테스트할 스킬 이름 (예: 자바스크립트 -> js)
            test_skill_name = "js" 
            
            logger.info(f"🧪 Testing get_or_create for: {test_skill_name}")
            
            try:
                # Full Flow Test (Find -> Match or Create -> Vector DB)
                skill_id = await normalizer.get_or_create(test_skill_name)
                
                logger.info(f"🎉 Result Skill ID: {skill_id}")
                
            except Exception as e:
                logger.error(f"❌ Error during test: {e}")
                await session.rollback()
                
        finally:
            pass
        break 

if __name__ == "__main__":
    asyncio.run(main())
