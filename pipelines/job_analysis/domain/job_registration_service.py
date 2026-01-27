import logging
import hashlib
from typing import Any, List, Optional
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession

from job_analysis.data.models import JobPost, JobMaster, JobMasterSkill, Company, Skill
from job_analysis.data.repository.job_post_repository import JobPostRepository
from job_analysis.data.repository.job_master_repository import JobMasterRepository
from job_analysis.data.repository.company_repository import CompanyRepository
from job_analysis.data.repository.skill_repository import SkillRepository
from job_analysis.data.vector_repository.job_vector_repo import JobVectorRepository
from job_analysis.normalizer.company_normalizer import CompanyNormalizer
from job_analysis.normalizer.skill_normalizer import SkillNormalizer
from shared.schema.job_posting import JobPostingAnalyzeResponse, RecruitmentPeriod
from job_analysis.domain.job_duplicate_checker import JobDuplicateChecker
from job_analysis.data.repository.dto import JobPostingWithRelations

logger = logging.getLogger(__name__)

class JobRegistrationService:
    """
    신규 채용 공고 등록 로직을 담당하는 도메인 서비스입니다.
    - 정규화 (Company, Skill)
    - 엔티티 생성 (Company, Skill, JobMaster, JobPost)
    - 연결 (JobMasterSkill)
    """

    def __init__(
        self,
        session: AsyncSession,
        job_post_repo: JobPostRepository,
        job_master_repo: JobMasterRepository,
        company_repo: CompanyRepository,
        skill_repo: SkillRepository,
        company_normalizer: CompanyNormalizer,
        skill_normalizer: SkillNormalizer,
        duplicate_checker: JobDuplicateChecker,
        job_vector_repo: JobVectorRepository
    ):
        self.session = session
        self.job_post_repo = job_post_repo
        self.job_master_repo = job_master_repo
        self.company_repo = company_repo
        self.skill_repo = skill_repo
        self.company_normalizer = company_normalizer
        self.skill_normalizer = skill_normalizer
        self.duplicate_checker = duplicate_checker
        self.job_vector_repo = job_vector_repo

    async def ensure_and_get_ids(self, extracted_data: Any) -> tuple[int, List[int], Any]:
        """
        회사와 스킬이 DB에 존재하는지 확인하고, 없으면 생성하여 ID를 반환합니다.
        또한 extracted_data의 내용을 정규화된 명칭(DB에 저장된 이름)으로 업데이트하여 반환합니다.
        """
        
        # 1. 회사 처리 (Get or Create)
        company_id = await self.company_normalizer.get_or_create(extracted_data.company_name)
        
        # 정규화된 회사명 조회 및 업데이트
        company = await self.company_repo.find_by_id(company_id)
        if company:
            extracted_data.company_name = company.name

        # 2. 스킬 처리 (Get or Create Batch)
        raw_skills = extracted_data.tech_stacks or []
        # 모든 스킬에 대해 ID를 보장받음
        final_skill_ids = await self.skill_normalizer.get_or_create_batch(raw_skills)
        
        normalized_skill_names = []

        # ID -> Name 역조회 (데이터 패치용)
        # TODO: 성능 최적화 (IN 쿼리 등) 필요하지만 지금은 안전하게 루프
        for skill_id, raw_skill in zip(final_skill_ids, raw_skills):
            skill = await self.skill_repo.find_by_id(skill_id)
            if skill:
                 normalized_skill_names.append(skill.skill_name)
            else:
                 # ID는 있는데 조회가 안되는 경우 (거의 없음)
                 normalized_skill_names.append(raw_skill)
        
        # 정규화된 스킬명으로 업데이트
        extracted_data.tech_stacks = normalized_skill_names
        
        return company_id, final_skill_ids, extracted_data

    async def register_new_job_master(
        self,
        url: str,
        extracted_data: Any,
        fingerprint: str,
        company_id: int,
        skill_ids: List[int]
    ) -> JobPostingWithRelations:
        """완전히 새로운 JobMaster와 JobPost를 생성합니다."""
        
        # Step 3: 신규 JobMaster 생성 (ID들은 이미 확보됨)
        logger.info("🆕 Creating new JobMaster")
        job_master = await self._create_job_master(
            company_id=company_id,
            extracted_data=extracted_data
        )
        
        # Step 4: JobMasterSkill 연결
        await self._link_skills_to_job_master(job_master.job_master_id, skill_ids)

        # Step 5: JobPost 생성
        job_post = await self._create_job_post(
            job_master_id=job_master.job_master_id,
            company_id=company_id,
            url=url,
            extracted_data=extracted_data,
            fingerprint=fingerprint
        )

        # Step 6: Vector DB 등록 (JobPost 기준)
        # Note: extracted_data는 이미 정규화된 상태입니다.
        try:
            json_text = extracted_data.model_dump_json()
            await self.job_vector_repo.add_job(
                job_master_id=job_master.job_master_id,
                job_post_id=job_post.job_post_id,
                company_id=company_id,
                content=json_text
            )
            logger.info(f"💾 Added JobPost {job_post.job_post_id} (Master {job_master.job_master_id}) to Vector DB")
        except Exception as e:
             logger.error(f"❌ Failed to add job to vector DB: {e}", exc_info=True)

        return await self._build_dto(job_post, job_master, company_id)

    async def link_job_post(
        self,
        job_master_id: int,
        url: str,
        extracted_data: Any,
        fingerprint: str
    ) -> JobPostingWithRelations:
        """기존 JobMaster에 새로운 JobPost를 연결합니다."""
        
        logger.info(f"🔗 Linking new JobPost to existing JobMaster ID: {job_master_id}")
        
        # JobMaster 조회
        job_master = await self.job_master_repo.find_by_id(job_master_id)
        if not job_master:
             raise ValueError(f"JobMaster {job_master_id} not found.")

        # 회사 ID 확보 (JobMaster의 회사)
        company_id = job_master.company_id

        # JobPost 생성
        job_post = await self._create_job_post(
            job_master_id=job_master_id,
            company_id=company_id,
            url=url,
            extracted_data=extracted_data,
            fingerprint=fingerprint
        )

        # Vector DB 등록 (중복 공고라도 개별 벡터를 저장하여 데이터 축적)
        try:
            json_text = extracted_data.model_dump_json()
            await self.job_vector_repo.add_job(
                job_master_id=job_master_id,
                job_post_id=job_post.job_post_id,
                company_id=company_id,
                content=json_text
            )
            logger.info(f"💾 Added JobPost {job_post.job_post_id} (Master {job_master_id}) to Vector DB")
        except Exception as e:
             logger.error(f"❌ Failed to add job to vector DB: {e}", exc_info=True)

        return await self._build_dto(job_post, job_master, company_id)



    async def _create_job_master(self, company_id: int, extracted_data: Any) -> JobMaster:
        """JobMaster를 생성합니다."""
        logger.info(f"📝 Creating JobMaster: {extracted_data.job_title}")

        start_date = None
        end_date = None

        if extracted_data.start_date:
            try:
                start_date = date.fromisoformat(extracted_data.start_date)
            except ValueError:
                pass

        if extracted_data.end_date:
            try:
                end_date = date.fromisoformat(extracted_data.end_date)
            except ValueError:
                pass

        new_job_master = JobMaster(
            company_id=company_id,
            job_title=extracted_data.job_title,
            main_tasks=extracted_data.main_tasks,
            ai_summary=extracted_data.ai_summary,
            evaluation_criteria=None,
            status="Open",
            start_date=start_date,
            end_date=end_date,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        return await self.job_master_repo.create(new_job_master)

    async def _link_skills_to_job_master(self, job_master_id: int, skill_ids: List[int]) -> None:
        """JobMaster와 Skills를 연결합니다."""
        if not skill_ids:
            return

        for skill_id in skill_ids:
            link = JobMasterSkill(
                job_master_id=job_master_id,
                skill_id=skill_id,
                created_at=datetime.now()
            )
            await self.skill_repo.create_job_master_skill(link)

    async def _create_job_post(self, job_master_id: int, company_id: int, url: str, extracted_data: Any, fingerprint: str) -> JobPost:
        """JobPost를 생성합니다."""
        logger.info(f"📝 Creating JobPost for URL: {url}")
        
        url_hash = hashlib.sha256(url.encode("utf-8")).hexdigest()

        new_job_post = JobPost(
            job_master_id=job_master_id,
            company_id=company_id,
            source_type="crawler",
            source_url=url,
            source_url_hash=url_hash,
            raw_company_name=extracted_data.company_name,
            raw_job_title=extracted_data.job_title,
            main_tasks=extracted_data.main_tasks,
            recruitment_status="Open",
            registration_status="Active",
            start_date=None,
            end_date=None,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            fingerprint_hash=fingerprint
        )
        return await self.job_post_repo.create(new_job_post)

    async def _build_dto(self, job_post: JobPost, job_master: JobMaster, company_id: int) -> JobPostingWithRelations:
        """DTO 반환"""
        company = await self.company_repo.find_by_id(company_id)
        skill_names = await self.skill_repo.find_names_by_job_master_id(job_master.job_master_id)

        # DTO 생성
        return JobPostingWithRelations(
            job_post=job_post,
            job_master=job_master,
            company=company,
            skills=skill_names
        )
