from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from shared.db.model.models import JobMaster, JobMasterSkill, Skill
from ...domain.interface.repository_interfaces import JobRepository
from ...domain.models.job import JobInfo, EvaluationCriteria


class SqlAlchemyJobRepository(JobRepository):
    """
    JobRepository의 SQLAlchemy (Async) 구현체
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_job_info(self, job_id: int) -> Optional[JobInfo]:
        # 1. JobMaster + Company 조회
        stmt = (
            select(JobMaster)
            .options(joinedload(JobMaster.company))
            .where(JobMaster.job_master_id == job_id)
        )
        result = await self.session.execute(stmt)
        job_master = result.scalars().first()

        if not job_master:
            return None

        # 2. Tech Stacks (Skills) 조회
        # JobMasterSkill 테이블과 Skill 테이블을 조인하여 스킬 이름만 가져옴
        msg_stmt = (
            select(Skill.skill_name)
            .join(JobMasterSkill, Skill.skill_id == JobMasterSkill.skill_id)
            .where(JobMasterSkill.job_master_id == job_id)
        )
        msg_result = await self.session.execute(msg_stmt)
        # scalars().all() -> ['Python', 'Java']
        tech_stacks = list(msg_result.scalars().all())

        # 3. Evaluation Criteria 변환 (JSON -> Domain Models)
        criteria_list = []
        if job_master.evaluation_criteria:
            criteria_data = job_master.evaluation_criteria
            if isinstance(criteria_data, list):
                criteria_list = [
                    EvaluationCriteria(
                        name=item.get("name", "Unknown"),
                        description=item.get("description", ""),
                    )
                    for item in criteria_data
                ]

        # 4. 도메인 객체 생성 및 반환
        return JobInfo(
            company_name=job_master.company.name if job_master.company else "Unknown",
            main_tasks=(
                job_master.main_tasks if isinstance(job_master.main_tasks, list) else []
            ),
            tech_stacks=tech_stacks,
            summary=job_master.ai_summary or "",
            evaluation_criteria=criteria_list,
        )
