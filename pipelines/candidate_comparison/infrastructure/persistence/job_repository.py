from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from ...domain.interface.repository_interfaces import JobRepository
from ...domain.models.job import JobInfo, EvaluationCriteria
from shared.db.model.models import JobMaster, JobMasterSkill, Skill


class SqlAlchemyJobRepository(JobRepository):
    """
    채용 공고 저장소 구현체 (Async)

    조회 데이터:
    - JobMaster (공고 기본 정보)
    - Company (회사 정보)
    - JobMasterSkill + Skill (기술 스택)
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_job(self, job_master_id: int) -> Optional[JobInfo]:
        """
        채용 공고 정보 조회

        Args:
            job_master_id: 공고 ID

        Returns:
            JobInfo: 공고 정보 + 평가 기준
        """
        # 1. JobMaster + Company 조회
        stmt = (
            select(JobMaster)
            .options(joinedload(JobMaster.company))
            .where(JobMaster.job_master_id == job_master_id)
        )
        result = await self.session.execute(stmt)
        job_master = result.scalars().first()

        if not job_master:
            return None

        # 2. Tech Stacks (Skills) 조회
        skill_stmt = (
            select(Skill.skill_name)
            .join(JobMasterSkill, Skill.skill_id == JobMasterSkill.skill_id)
            .where(JobMasterSkill.job_master_id == job_master_id)
        )
        skill_result = await self.session.execute(skill_stmt)
        tech_stacks = list(skill_result.scalars().all())

        # 3. Evaluation Criteria 변환 (JSON → Domain Models)
        criteria_list = self._parse_evaluation_criteria(
            job_master.evaluation_criteria  # type: ignore
        )

        # 4. 도메인 객체 생성
        return JobInfo(
            job_posting_id=str(job_master.job_master_id),
            job_title=str(job_master.job_title or ""),
            company_name=job_master.company.name if job_master.company else "Unknown",
            main_tasks=(
                job_master.main_tasks if isinstance(job_master.main_tasks, list) else []
            ),
            tech_stacks=tech_stacks,
            summary=str(job_master.ai_summary or ""),
            evaluation_criteria=criteria_list,
        )

    def _parse_evaluation_criteria(
        self, criteria_json: any
    ) -> list[EvaluationCriteria]:
        """
        JSON 평가 기준을 EvaluationCriteria 리스트로 변환

        evaluation_criteria JSON 구조:
        [
            {"name": "기술 역량", "description": "..."},
            {"name": "직무 적합성", "description": "..."}
        ]

        Args:
            criteria_json: DB에 저장된 JSON 데이터

        Returns:
            list[EvaluationCriteria]: 평가 기준 리스트
        """
        if not criteria_json:
            return []

        if not isinstance(criteria_json, list):
            return []

        criteria = []
        for item in criteria_json:
            if isinstance(item, dict):
                criteria.append(
                    EvaluationCriteria(
                        name=item.get("name", "Unknown"),
                        description=item.get("description", ""),
                    )
                )

        return criteria
