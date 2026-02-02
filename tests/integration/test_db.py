import asyncio
import logging
import sys
import os

# 현재 디렉토리를 path에 추가하여 모듈 인식 가능하게 함
sys.path.append(os.getcwd())

from sqlalchemy import text
from shared.db.connection import get_db
from job_analysis.data.repository import JobPostRepository

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DB_TEST")


async def test_connection():
    logger.info("📡 Testing DB Connection...")
    async for session in get_db():
        try:
            # 1. 단순 연결 테스트 (SELECT 1)
            result = await session.execute(text("SELECT 1"))
            val = result.scalar()
            logger.info(f"✅ Connection Successful! (SELECT 1 => {val})")

            # 2. Repository 조회 테스트 (SQL 매핑 확인)
            repo = JobPostRepository(session)
            # 존재하지 않는 ID로 조회하여 에러가 안 나는지 확인
            post = await repo.find_by_id(999999999)
            logger.info(f"✅ Repository Read Test Passed. Result: {post}")

        except Exception as e:
            logger.error(f"❌ DB Error: {e}")
            # 자세한 에러 출력을 위해
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    try:
        asyncio.run(test_connection())
    except KeyboardInterrupt:
        pass
