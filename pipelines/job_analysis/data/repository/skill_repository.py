from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from job_analysis.data.models import Skill, JobMasterSkill


class SkillRepository:
    """Skill 테이블 전용 Repository (CRUD)"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, skill: Skill) -> Skill:
        """새로운 스킬을 저장합니다."""
        self.session.add(skill)
        await self.session.commit()
        await self.session.refresh(skill)
        return skill

    async def find_by_id(self, skill_id: int) -> Optional[Skill]:
        """ID로 스킬을 조회합니다."""
        stmt = select(Skill).where(Skill.skill_id == skill_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def find_by_name(self, skill_name: str) -> Optional[Skill]:
        """이름으로 스킬을 조회합니다."""
        stmt = select(Skill).where(Skill.skill_name == skill_name).where(Skill.deleted_at.is_(None))
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def find_names_by_job_master_id(self, job_master_id: int) -> List[str]:
        """JobMaster ID로 연결된 스킬 이름 목록을 조회합니다."""
        stmt = (
            select(Skill.skill_name)
            .join(JobMasterSkill, JobMasterSkill.skill_id == Skill.skill_id)
            .where(JobMasterSkill.job_master_id == job_master_id)
            .where(JobMasterSkill.deleted_at.is_(None))
            .where(Skill.deleted_at.is_(None))
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create_job_master_skill(self, job_master_skill: JobMasterSkill) -> JobMasterSkill:
        """JobMaster와 Skill 연결을 생성합니다."""
        self.session.add(job_master_skill)
        await self.session.commit()
        await self.session.refresh(job_master_skill)
        return job_master_skill
