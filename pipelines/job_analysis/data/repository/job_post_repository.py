from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from job_analysis.data.models import JobPost


class JobPostRepository:
    """JobPost 테이블 전용 Repository (CRUD)"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, job_post: JobPost) -> JobPost:
        """새로운 채용 공고를 저장합니다."""
        self.session.add(job_post)
        await self.session.flush()
        return job_post

    async def find_by_id(self, job_post_id: int) -> Optional[JobPost]:
        """ID로 채용 공고를 조회합니다."""
        stmt = select(JobPost).where(JobPost.job_post_id == job_post_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def find_by_url(self, source_url: str) -> Optional[JobPost]:
        """URL을 기준으로 채용 공고를 조회합니다."""
        stmt = select(JobPost).where(JobPost.source_url == source_url)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def find_by_fingerprint(self, fingerprint_hash: str) -> Optional[JobPost]:
        """Fingerprint로 채용 공고를 조회합니다."""
        stmt = select(JobPost).where(JobPost.fingerprint_hash == fingerprint_hash)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def delete_by_master_id(self, job_master_id: int) -> None:
        """JobMaster ID에 연결된 모든 JobPost를 물리 삭제합니다."""
        from sqlalchemy import delete
        stmt = delete(JobPost).where(JobPost.job_master_id == job_master_id)
        await self.session.execute(stmt)
