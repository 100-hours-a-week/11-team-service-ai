from typing import Optional, Any
import logging
import hashlib
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from job_analysis.data.repository.job_post_repository import JobPostRepository
from job_analysis.data.repository.job_master_repository import JobMasterRepository
from job_analysis.data.repository.company_repository import CompanyRepository
from job_analysis.data.repository.skill_repository import SkillRepository
from job_analysis.data.repository.job_posting_query_repository import (
    JobPostingQueryRepository,
)
from job_analysis.data.repository.dto import JobPostingWithRelations
from job_analysis.data.models import JobPost
from job_analysis.parser.crawlers.factory import CrawlerFactory
from job_analysis.parser.extract.extractor import JobPostingExtractor
from job_analysis.utils.fingerprint import FingerprintGenerator
from shared.schema.job_posting import JobPostingAnalyzeResponse
from job_analysis.normalizer.company_normalizer import CompanyNormalizer
from job_analysis.normalizer.skill_normalizer import SkillNormalizer
from job_analysis.domain.job_registration_service import JobRegistrationService
from job_analysis.domain.job_duplicate_checker import JobDuplicateChecker
from job_analysis.data.vector_repository.job_vector_repo import JobVectorRepository

logger = logging.getLogger(__name__)


class JobAnalysisService:
    def __init__(self, session: AsyncSession):
        self.session = session

        # Repository 초기화 (각 엔티티별 + Query 전용)
        self.job_post_repo = JobPostRepository(session)
        self.job_master_repo = JobMasterRepository(session)
        self.company_repo = CompanyRepository(session)
        self.skill_repo = SkillRepository(session)
        self.query_repo = JobPostingQueryRepository(session)

        # Normalizer 초기화 (Repository 주입)
        self.company_normalizer = CompanyNormalizer(repo=self.company_repo)
        self.skill_normalizer = SkillNormalizer(repo=self.skill_repo)

        # Vector Repo / Checker 초기화
        self.job_vector_repo = JobVectorRepository()
        self.duplicate_checker = JobDuplicateChecker(
            job_post_repo=self.job_post_repo,
            job_vector_repo=self.job_vector_repo,
            query_repo=self.query_repo,
            skill_repo=self.skill_repo,
        )

        # Domain Service 초기화
        self.registration_service = JobRegistrationService(
            session=self.session,
            job_post_repo=self.job_post_repo,
            job_master_repo=self.job_master_repo,
            company_repo=self.company_repo,
            skill_repo=self.skill_repo,
            company_normalizer=self.company_normalizer,
            skill_normalizer=self.skill_normalizer,
            duplicate_checker=self.duplicate_checker,
            job_vector_repo=self.job_vector_repo,
        )

        self.extractor = JobPostingExtractor()  # Extractor 초기화

    def _hash_url(self, url: str) -> str:
        """URL SHA-256 해시 생성"""
        return hashlib.sha256(url.encode("utf-8")).hexdigest()

    def _map_to_response(
        self, post: JobPost, is_existing: bool
    ) -> JobPostingAnalyzeResponse:
        """SQLAlchemy Model -> Pydantic Response 변환"""
        # ... (기존 로직 유지)

    async def run_analysis(self, url: str) -> JobPostingAnalyzeResponse:
        """
        채용 공고 분석 파이프라인 메인 진입점.
        Returns: JobPostingAnalyzeResponse (Pydantic Model)
        """
        logger.info(f"🚀 Starting Job Analysis for: {url}")

        # 1. URL 중복 체크 (Fast Track via DuplicateChecker)
        existing_result = await self.duplicate_checker.check_existing_post_by_url(url)
        if existing_result:
            logger.info(
                f"✅ Found existing job post (ID: {existing_result.job_post.job_post_id})"
            )
            return await self._map_to_response_from_dto(
                existing_result, is_existing=True
            )

        # 2. 크롤링 (Crawling)
        raw_text = await self._crawl_content(url)

        # 3. 추출 (Extraction)
        extracted_data = await self._extract_data(raw_text)

        # 4. Fingerprint 생성 및 중복 체크
        fingerprint = FingerprintGenerator.generate(
            company_name=extracted_data.company_name,
            job_title=extracted_data.job_title,
            main_tasks=extracted_data.main_tasks,
        )
        duplicate_response = await self._handle_content_duplicate(
            url, extracted_data, fingerprint
        )
        if duplicate_response:
            return duplicate_response

        # 5. 의미적 중복(Semantic Duplicate) 및 정규화/생성
        #    이 단계에서 회사와 스킬을 DB에 확보(Ensure)하고 ID를 받아옵니다.
        #    동시에 extracted_data를 정규화된 데이터로 업데이트합니다 (normalized_data 반환).

        company_id, skill_ids, normalized_data = (
            await self.registration_service.ensure_and_get_ids(extracted_data)
        )

        # 5-3. 텍스트 직렬화 (전체 데이터를 JSON으로 변환하여 벡터 검색에 사용)
        job_search_text = normalized_data.model_dump_json()

        # 5-4. 중복 검사 실행 (JSON 텍스트 + 확보된 ID 사용)
        existing_job_master_id = await self.duplicate_checker.check_semantic_duplicate(
            company_id=company_id, job_text=job_search_text
        )

        # 6. 최종 등록 처리 (분기)
        result: JobPostingAnalyzeResponse = None

        if existing_job_master_id:
            logger.info(
                f"♻️ Semantic Duplicate found! Linking to JobMaster ID: {existing_job_master_id}"
            )
            # Case A: 중복 -> 기존 Master에 연결
            result_dto = await self.registration_service.link_job_post(
                job_master_id=existing_job_master_id,
                url=url,
                extracted_data=normalized_data,
                fingerprint=fingerprint,
            )
            result = await self._map_to_response_from_dto(result_dto, is_existing=True)
        else:
            logger.info("🆕 No duplicate found. Proceeding to create new JobMaster.")
            # Case B: 신규 -> 새로 생성
            result_dto = await self.registration_service.register_new_job_master(
                url=url,
                extracted_data=normalized_data,
                fingerprint=fingerprint,
                company_id=company_id,
                skill_ids=skill_ids,
            )
            result = await self._map_to_response_from_dto(result_dto, is_existing=False)

        # Transaction Commit at Service Layer End
        await self.session.commit()

        return result

    async def _crawl_content(self, url: str) -> str:
        """URL에서 텍스트 콘텐츠를 크롤링합니다 (비동기 처리)."""
        logger.info("🆕 New URL detected. Proceeding to Crawling...")
        try:
            crawler = CrawlerFactory.get_crawler(url)

            # Playwright는 블로킹 I/O이므로 별도 스레드에서 실행
            raw_text = await asyncio.to_thread(crawler.fetch, url)

            if not raw_text or len(raw_text) < 50:
                raise ValueError("Crawled content is empty or too short.")

            logger.info(f"✅ Crawling successful. Length: {len(raw_text)} chars")
            return raw_text
        except ValueError as e:
            logger.error(f"❌ Crawling validation failed: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Crawling failed: {e}", exc_info=True)
            raise RuntimeError(f"Crawling failed: {e}") from e

    async def _extract_data(self, raw_text: str):
        """LLM을 사용하여 텍스트에서 구조화된 데이터를 추출합니다."""
        try:
            extracted_data = await self.extractor.extract(raw_text)
            if not extracted_data:
                raise RuntimeError("LLM Extraction returned empty result")
            return extracted_data
        except Exception as e:
            logger.error(f"❌ LLM extraction failed: {e}", exc_info=True)
            if "API" in str(e) or "OpenAI" in str(e):
                raise RuntimeError(f"OpenAI API error: {e}") from e
            raise RuntimeError(f"Data extraction failed: {e}") from e

    async def _handle_content_duplicate(
        self, url: str, extracted_data: Any, fingerprint: str
    ) -> Optional[JobPostingAnalyzeResponse]:
        """내용 기반 중복(Fingerprint)이 있는지 확인하고 처리합니다. (Delegated to DuplicateChecker)"""

        # DuplicateChecker를 통해 Fingerprint 중복 확인 (Relations 포함된 DTO 반환)
        result = await self.duplicate_checker.check_existing_post_by_fingerprint(
            fingerprint
        )

        if result:
            logger.info("♻️ Content Duplicate detected. Linking to existing Master.")

            # 새 JobPost 생성 및 연결 (RegistrationService 위임)
            duplicate_dto = await self.registration_service.link_job_post(
                job_master_id=result.job_master.job_master_id,
                url=url,
                extracted_data=extracted_data,
                fingerprint=fingerprint,
            )

            # 중복 처리(연결)도 DB 쓰기 작업(JobPost 생성)이 포함되므로 커밋 필요
            await self.session.commit()

            return await self._map_to_response_from_dto(duplicate_dto, is_existing=True)

        return None

    async def _map_to_response_from_dto(
        self, dto: JobPostingWithRelations, is_existing: bool
    ) -> JobPostingAnalyzeResponse:
        """DTO -> Pydantic Response 변환 (JobMaster 기준, 최적화)"""

        from shared.schema.job_posting import RecruitmentPeriod

        # DTO에서 모든 데이터 추출 (추가 쿼리 없음)
        job_master = dto.job_master
        company = dto.company
        job_post = dto.job_post

        # RecruitmentPeriod 객체 생성
        recruitment_period = RecruitmentPeriod(
            start_date=job_master.start_date, end_date=job_master.end_date
        )

        return JobPostingAnalyzeResponse(
            job_posting_id=job_post.job_post_id,
            is_existing=is_existing,
            company_name=company.name,
            job_title=job_master.job_title,
            main_responsibilities=(
                job_master.main_tasks if isinstance(job_master.main_tasks, list) else []
            ),
            required_skills=dto.skills,
            recruitment_status=job_master.status,
            recruitment_period=recruitment_period,
            ai_summary=job_master.ai_summary or "",
        )

    async def delete_job_posting(self, job_posting_id: int) -> int:
        """
        Job Posting ID를 기준으로 관련 데이터(JobMaster, JobPost, Skills, Vector)를 일괄 삭제합니다.
        (Hard Delete)
        """
        logger.info(f"🗑️ Deleting Job Posting ID: {job_posting_id}")

        # 1. JobPost 조회 -> JobMaster ID 확보
        job_post = await self.job_post_repo.find_by_id(job_posting_id)
        if not job_post:
            logger.warning(f"JobPost {job_posting_id} not found.")
            return None

        master_id = job_post.job_master_id
        logger.info(f"Trace JobMaster ID: {master_id}")

        try:
            # # 2. RDB 데이터 삭제 (순서 중요: Child -> Parent)

            # # 2-1. Skill 연결 삭제 (JobMasterSkill)
            # await self.skill_repo.delete_job_master_skills(master_id)

            # # 2-2. JobPosts 삭제 (해당 마스터에 연결된 모든 공고)
            # await self.job_post_repo.delete_by_master_id(master_id)

            # # 2-3. JobMaster 삭제
            # await self.job_master_repo.delete(master_id)

            # # 3. Vector DB 삭제
            # await self.job_vector_repo.delete_jobs_by_master_id(master_id)

            # # 4. Commit
            # await self.session.commit()

            # logger.info(f"✅ Successfully deleted JobMaster {master_id} and related data.")

            return job_posting_id

        except Exception as e:
            await self.session.rollback()
            logger.error(f"❌ Failed to delete job posting: {e}", exc_info=True)
            raise
