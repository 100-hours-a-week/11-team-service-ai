import asyncio
import logging
import uuid
from typing import Any

from shared.db.connection import get_db
from job_analysis.service import JobAnalysisService
from job_analysis.parser.extract.extractor import ExtractedJobData
from job_analysis.data.models import JobPost

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mock Data
DUMMY_EXTRACTED_DATA = ExtractedJobData(
    company_name="DeleteTestCompany",
    job_title="Delete Test Job",
    tech_stacks=["python", "test"],
    main_tasks=["Testing deletion"],
    ai_summary="This is a test job for deletion.",
    qualification_requirements=["None"],
    preferred_qualifications=["None"],
    start_date="2026-01-26",
    end_date="2026-02-28"
)

class MockJobAnalysisService(JobAnalysisService):
    async def _crawl_content(self, url: str) -> str:
        return "MOCK_HTML_CONTENT"

    async def _extract_data(self, raw_text: str):
        return DUMMY_EXTRACTED_DATA

async def main():
    logger.info("🚀 Starting Deletion Test...")
    
    unique_id = uuid.uuid4().hex[:8]
    test_url = f"https://www.test.com/delete_test/{unique_id}"

    async for session in get_db():
        service = MockJobAnalysisService(session)
        created_id = None
        
        try:
            # 1. Create Job
            logger.info("1. Creating Job...")
            response = await service.run_analysis(test_url)
            created_id = response.job_posting_id
            logger.info(f"✅ Job Created with ID: {created_id}")
            
            # Verify Creation
            job = await service.job_repo.find_by_id(created_id)
            if not job:
                logger.error("❌ Job not found in DB immediately after creation (Logic Error)")
                return
            logger.info("✅ Verified Job exists in DB")
            
            # 2. Delete Job
            logger.info("2. Deleting Job...")
            # We use the base service's deletion method
            delete_response = await service.delete_job_posting(created_id)
            logger.info(f"✅ Delete returned ID: {delete_response.deleted_id}")

            # 3. Verify Deletion
            logger.info("3. Verifying Deletion...")
            
            # Check RDB
            job_after = await service.job_repo.find_by_id(created_id)
            if job_after:
                logger.error(f"❌ Job {created_id} STILL EXISTS in RDB!")
            else:
                logger.info("✅ Job gone from RDB")

        except Exception as e:
            logger.error(f"❌ Test Failed: {e}", exc_info=True)
            await session.rollback()
        
        break # One pass

if __name__ == "__main__":
    asyncio.run(main())
