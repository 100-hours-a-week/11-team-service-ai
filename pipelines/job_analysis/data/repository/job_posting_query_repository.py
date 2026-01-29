from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from job_analysis.data.models import JobPost, JobMaster, Company, Skill, JobMasterSkill
from job_analysis.data.repository.dto import JobPostingWithRelations


class JobPostingQueryRepository:
    """복잡한 JOIN 조회 쿼리 전용 Repository (읽기 전용)"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_with_relations_by_url(
        self, source_url: str
    ) -> Optional[JobPostingWithRelations]:
        """URL로 JobPost, JobMaster, Company, Skills를 한 번에 조회 (최적화된 JOIN 쿼리)"""

        # 1. JobPost + JobMaster + Company를 JOIN으로 조회
        stmt = (
            select(JobPost, JobMaster, Company)
            .join(JobMaster, JobPost.job_master_id == JobMaster.job_master_id)
            .join(Company, JobPost.company_id == Company.company_id)
            .where(JobPost.source_url == source_url)
            .where(JobPost.deleted_at.is_(None))
            .where(JobMaster.deleted_at.is_(None))
            .where(Company.deleted_at.is_(None))
        )

        result = await self.session.execute(stmt)
        row = result.first()

        if not row:
            return None

        job_post, job_master, company = row

        # 2. Skills 조회 (별도 쿼리 - 하지만 총 2회로 단축)
        skills = await self._get_skills_by_job_master_id(job_master.job_master_id)

        return JobPostingWithRelations(
            job_post=job_post,
            job_master=job_master,
            company=company,
            skills=skills
        )

    async def find_with_relations_by_fingerprint(
        self, fingerprint_hash: str
    ) -> Optional[JobPostingWithRelations]:
        """Fingerprint로 JobPost, JobMaster, Company, Skills를 한 번에 조회 (최적화된 JOIN 쿼리)"""

        # 1. JobPost + JobMaster + Company를 JOIN으로 조회
        stmt = (
            select(JobPost, JobMaster, Company)
            .join(JobMaster, JobPost.job_master_id == JobMaster.job_master_id)
            .join(Company, JobPost.company_id == Company.company_id)
            .where(JobPost.fingerprint_hash == fingerprint_hash)
            .where(JobPost.deleted_at.is_(None))
            .where(JobMaster.deleted_at.is_(None))
            .where(Company.deleted_at.is_(None))
        )

        result = await self.session.execute(stmt)
        row = result.first()

        if not row:
            return None

        job_post, job_master, company = row

        # 2. Skills 조회
        skills = await self._get_skills_by_job_master_id(job_master.job_master_id)

        return JobPostingWithRelations(
            job_post=job_post,
            job_master=job_master,
            company=company,
            skills=skills
        )

    async def _get_skills_by_job_master_id(self, job_master_id: int) -> List[str]:
        """내부 헬퍼: JobMaster ID로 연결된 스킬 목록을 조회"""
        stmt = (
            select(Skill.skill_name)
            .join(JobMasterSkill, JobMasterSkill.skill_id == Skill.skill_id)
            .where(JobMasterSkill.job_master_id == job_master_id)
            .where(JobMasterSkill.deleted_at.is_(None))
            .where(Skill.deleted_at.is_(None))
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
