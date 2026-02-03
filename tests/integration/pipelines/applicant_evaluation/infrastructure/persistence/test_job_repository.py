
import pytest
from datetime import date
from shared.db.model.models import Company, JobMaster, Skill, JobMasterSkill
from pipelines.applicant_evaluation.infrastructure.persistence.job_repository import SqlAlchemyJobRepository
from pipelines.applicant_evaluation.domain.models.job import JobInfo

@pytest.mark.asyncio
async def test_get_job_info_found(db_session):
    """
    DB에 저장된 JobMaster 데이터를 레포지토리 조회를 통해 JobInfo 도메인 객체로 잘 변환하는지 테스트
    """
    # 1. Setup Data
    repo = SqlAlchemyJobRepository(db_session)
    
    # 1-1. Company
    company = Company(name="IntegrationTest Corp", domain="test.com")
    db_session.add(company)
    await db_session.flush() 
    
    # 1-2. Tech Stack (Skill)
    skill_python = Skill(skill_name="Python", category="Language")
    db_session.add(skill_python)
    await db_session.flush()

    # 1-3. JobMaster
    job_master = JobMaster(
        company_id=company.company_id,
        job_title="Backend Engineer",
        main_tasks=["API Dev", "DB Design"], 
        evaluation_criteria=[
            {"name": "직무적합성", "description": "기술 스택 일치 여부"},
            {"name": "성장가능성", "description": "학습 의지"}
        ],
        status="OPEN",
        start_date=date(2025, 1, 1),
        end_date=date(2025, 12, 31),
        ai_summary="This is a summary"
    )
    db_session.add(job_master)
    await db_session.flush()

    # 1-4. Map Skill to Job (relation)
    job_skill = JobMasterSkill(job_master_id=job_master.job_master_id, skill_id=skill_python.skill_id)
    db_session.add(job_skill)
    await db_session.commit()

    # 2. Execute
    result = await repo.get_job_info(job_master.job_master_id)

    # 3. Verify
    assert result is not None
    assert isinstance(result, JobInfo)
    assert result.company_name == "IntegrationTest Corp"
    assert "Python" in result.tech_stacks
    assert len(result.evaluation_criteria) == 2
    assert result.evaluation_criteria[0].name == "직무적합성"

@pytest.mark.asyncio
async def test_get_job_info_not_found(db_session):
    """
    존재하지 않는 ID 조회 시 None 반환
    """
    repo = SqlAlchemyJobRepository(db_session)
    result = await repo.get_job_info(999999) # Non-existent ID
    assert result is None
