from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from job_analysis.data.models import JobMaster


class JobMasterRepository:
    """JobMaster 테이블 전용 Repository (CRUD)"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, job_master: JobMaster) -> JobMaster:
        """새로운 JobMaster를 저장합니다."""
        self.session.add(job_master)
        await self.session.flush()
        return job_master

    async def find_by_id(self, job_master_id: int) -> Optional[JobMaster]:
        """ID로 JobMaster를 조회합니다."""
        stmt = select(JobMaster).where(JobMaster.job_master_id == job_master_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def update(self, job_master: JobMaster) -> JobMaster:
        """JobMaster를 업데이트합니다."""
        await self.session.flush()
        return job_master

    async def delete(self, job_master_id: int) -> None:
        """JobMaster를 물리 삭제합니다."""
        from sqlalchemy import delete

        stmt = delete(JobMaster).where(JobMaster.job_master_id == job_master_id)
        await self.session.execute(stmt)
