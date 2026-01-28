from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from ai.shared.db.model.models import JobMaster, Company, JobMasterSkill, Skill
from ...domain.interface.repository_interfaces import JobRepository
from ...domain.models.job import JobInfo, EvaluationCriteria

class SqlAlchemyJobRepository(JobRepository):
    """
    JobRepository의 SQLAlchemy 구현체
    """
    def __init__(self, session: Session):
        self.session = session

    def get_job_info(self, job_id: int) -> Optional[JobInfo]:
        # ORM 쿼리: JobMaster를 조회하면서 Company와 Skill 정보를 함께 로딩
        # (N+1 문제 방지를 위해 joinedload 사용 권장, 여기선 명시적 조인으로 처리)
        
        # 1. JobMaster + Company 조회
        job_master: JobMaster = (
            self.session.query(JobMaster)
            .options(joinedload(JobMaster.company))  # 회사 정보 함께 로딩
            .filter(JobMaster.job_master_id == job_id)
            .one_or_none()
        )
        
        if not job_master:
            return None

        # 2. Tech Stacks (Skills) 조회
        # JobMasterSkill 테이블과 Skill 테이블을 조인하여 스킬 이름만 가져옴
        skills: List[str] = (
            self.session.query(Skill.skill_name)
            .join(JobMasterSkill, Skill.skill_id == JobMasterSkill.skill_id)
            .filter(JobMasterSkill.job_master_id == job_id)
            .all()
        )
        # 쿼리 결과가 [('Python',), ('Java',)] 형태이므로 list comprehension으로 변환
        tech_stacks = [s[0] for s in skills]

        # 3. Evaluation Criteria 변환 (JSON -> Domain Models)
        criteria_list = []
        if job_master.evaluation_criteria:
            # DB의 JSON 필드 구조가 리스트라고 가정
            # 예: [{"name": "직무적합성", "description": "..."}]
            criteria_data = job_master.evaluation_criteria
            if isinstance(criteria_data, list):
                criteria_list = [
                    EvaluationCriteria(
                        name=item.get('name', 'Unknown'),
                        description=item.get('description', '')
                    )
                    for item in criteria_data
                ]

        # 4. 도메인 객체 생성 및 반환
        return JobInfo(
            company_name=job_master.company.name if job_master.company else "Unknown",
            main_tasks=job_master.main_tasks if isinstance(job_master.main_tasks, list) else [],
            tech_stacks=tech_stacks,
            summary=job_master.ai_summary or "",
            evaluation_criteria=criteria_list
        )
