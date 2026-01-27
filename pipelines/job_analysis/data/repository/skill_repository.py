from typing import Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from job_analysis.data.models import Skill, JobMasterSkill, SkillAlias


class SkillRepository:
    """Skill 테이블 전용 Repository (CRUD)"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, skill: Skill) -> Skill:
        """새로운 스킬을 저장합니다."""
        self.session.add(skill)
        # Service 레벨에서 Transaction을 관리하도록 commit 제거
        await self.session.flush()
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

    async def find_ids_by_job_master_id(self, job_master_id: int) -> List[int]:
        """JobMaster ID로 연결된 스킬 ID 목록을 조회합니다."""
        stmt = (
            select(Skill.skill_id)
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
        await self.session.flush()
        return job_master_skill

    async def find_alias_by_name(self, raw_name: str) -> Optional[SkillAlias]:
        """별칭(Alias)으로 스킬을 조회합니다."""
        # 1. Skill 테이블에서 정확히 일치하는 이름 검색
        stmt = select(Skill).where(Skill.skill_name == raw_name).where(Skill.deleted_at.is_(None))
        result = await self.session.execute(stmt)
        skill = result.scalars().first()

        if skill:
            return SkillAlias(
                skill_id=skill.skill_id,
                alias_name=skill.skill_name,
                alias_normalized=skill.skill_name
            )

        # 2. SkillAlias 테이블 검색
        stmt = select(SkillAlias).where(SkillAlias.alias_name == raw_name).where(SkillAlias.deleted_at.is_(None))
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def add_alias(self, skill_id: int, raw_name: str) -> SkillAlias:
        """기존 스킬에 새로운 별칭을 추가합니다."""
        alias = SkillAlias(
            skill_id=skill_id,
            alias_name=raw_name,
            alias_normalized=raw_name.strip().lower(), # 간단한 정규화
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        self.session.add(alias)
        await self.session.flush()
        return alias

    async def delete_job_master_skills(self, job_master_id: int) -> None:
        """JobMaster ID에 연결된 모든 스킬 연결(JobMasterSkill)을 물리 삭제합니다."""
        from sqlalchemy import delete
        stmt = delete(JobMasterSkill).where(JobMasterSkill.job_master_id == job_master_id)
        await self.session.execute(stmt)
