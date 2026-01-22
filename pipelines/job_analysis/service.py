from typing import Optional, Any
import logging
import hashlib
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from job_analysis.data.repository.job_post_repository import JobPostRepository
from job_analysis.data.repository.job_master_repository import JobMasterRepository
from job_analysis.data.repository.company_repository import CompanyRepository
from job_analysis.data.repository.skill_repository import SkillRepository
from job_analysis.data.repository.job_posting_query_repository import JobPostingQueryRepository
from job_analysis.data.repository.dto import JobPostingWithRelations
from job_analysis.data.models import JobPost, JobMaster
from job_analysis.parser.crawlers.factory import CrawlerFactory
from job_analysis.parser.extract.extractor import JobPostingExtractor
from job_analysis.utils.fingerprint import FingerprintGenerator
from shared.schema.job_posting import JobPostingAnalyzeResponse

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

        self.extractor = JobPostingExtractor() # Extractor 초기화

    def _hash_url(self, url: str) -> str:
        """URL SHA-256 해시 생성"""
        return hashlib.sha256(url.encode("utf-8")).hexdigest()

    def _map_to_response(self, post: JobPost, is_existing: bool) -> JobPostingAnalyzeResponse:
        """SQLAlchemy Model -> Pydantic Response 변환"""
        # ... (기존 로직 유지)

    async def run_analysis(self, url: str) -> JobPostingAnalyzeResponse:
        """
        채용 공고 분석 파이프라인 메인 진입점.
        Returns: JobPostingAnalyzeResponse (Pydantic Model)
        """
        logger.info(f"🚀 Starting Job Analysis for: {url}")

        # 1. URL 중복 체크 (Fast Track)
        existing_result = await self.query_repo.find_with_relations_by_url(url)
        if existing_result:
            logger.info(f"✅ Found existing job post (ID: {existing_result.job_post.job_post_id}). Returning cached result.")
            return await self._map_to_response_from_dto(existing_result, is_existing=True)

        # 2. 크롤링 (Crawling)
        raw_text = self._crawl_content(url)

        # 3. 추출 (Extraction)
        extracted_data = await self._extract_data(raw_text)

        # 4. Fingerprint 생성 및 중복 체크
        fingerprint = FingerprintGenerator.generate(
            company_name=extracted_data.company_name,
            job_title=extracted_data.job_title,
            main_tasks=extracted_data.main_tasks
        )
        
        # 5. 기존 콘텐츠 중복 처리
        duplicate_response = await self._process_if_duplicate_exists(url, extracted_data, fingerprint)
        if duplicate_response:
            return duplicate_response


        # 6. 정규화 처리(회사명, 스킬셋) -> company, company_alias, skills, skills_alias 테이블 활용
        # 우선 회사부터 db조회 -> 없으면 벡터db조회 -> 유사도를 확인하여 높음, 낮음, 애매함으로 구분 -> 높으면 바로 매핑, 낮으면 신규 용어 등록, 애매하면 에이전트에게 요청

        # 그리고 스킬셋 각각에 대해 db조회 -> 없으면 벡터db조회 -> 유사도를 확인하여 높음, 낮음, 애매함으로 구분 -> 높으면 바로 매핑, 낮으면 신규 용어 등록 -> 애매하면 에이전트에게 요청

        # 벡터db는 전처리된 데이터가 존재? or 전처리되지 않은 데이터 존재? -> 전처리되지 않으면 유사도가 정확하게 측정 불가, 유사도 측정 정확도를 높이기 위해 전처리 후 벡터 db에 저장

        # 6. 신규 콘텐츠 처리 (완전 신규 공고)
        return await self._process_new_content(url, extracted_data, fingerprint)


    def _crawl_content(self, url: str) -> str:
        """[TODO] URL에서 텍스트 콘텐츠를 크롤링합니다."""
        logger.info("🆕 New URL detected. Proceeding to Crawling...")
        try:
            crawler = CrawlerFactory.get_crawler(url)
            raw_text = crawler.fetch(url)
            
            if not raw_text or len(raw_text) < 50:
                raise ValueError("Crawled content is empty or too short.")
                
            logger.info(f"✅ Crawling successful. Length: {len(raw_text)} chars")
            return raw_text
        except Exception as e:
            logger.error(f"❌ Crawling failed: {e}")
            raise RuntimeError(f"Crawling failed: {e}")

    async def _extract_data(self, raw_text: str):
        """ LLM을 사용하여 텍스트에서 구조화된 데이터를 추출합니다."""
        extracted_data = await self.extractor.extract(raw_text)
        if not extracted_data:
            raise RuntimeError("LLM Extraction failed.")
        return extracted_data

    async def _process_if_duplicate_exists(self, url: str, extracted_data: Any, fingerprint: str) -> Optional[JobPostingAnalyzeResponse]:
        """내용 기반 중복(Fingerprint)이 있는지 확인하고 처리합니다. (최적화된 JOIN 쿼리)"""

        # 최적화: 한 번의 JOIN 쿼리로 모든 데이터 조회
        # fingerprint와 일치하는 공고를 조회함
        result = await self.query_repo.find_with_relations_by_fingerprint(fingerprint)

        if result:
            logger.info(f"♻️ Content Duplicate detected. Linking to existing Master.")

            # 새 JobPost 생성 (URL은 다르지만 내용은 동일)
            new_job_post = JobPost(
                job_master_id=result.job_master.job_master_id,
                company_id=result.job_post.company_id,
                source_type="crawler",
                source_url=url,
                source_url_hash=self._hash_url(url),
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

            saved_post = await self.job_post_repo.create(new_job_post)

            # DTO 업데이트하여 재사용
            result.job_post = saved_post
            return await self._map_to_response_from_dto(result, is_existing=True)

        return None

    async def _map_to_response_from_dto(
        self,
        dto: JobPostingWithRelations,
        is_existing: bool
    ) -> JobPostingAnalyzeResponse:
        """DTO -> Pydantic Response 변환 (JobMaster 기준, 최적화)"""

        from shared.schema.job_posting import RecruitmentPeriod

        # DTO에서 모든 데이터 추출 (추가 쿼리 없음)
        job_master = dto.job_master
        company = dto.company
        job_post = dto.job_post

        # RecruitmentPeriod 객체 생성
        recruitment_period = RecruitmentPeriod(
            start_date=job_master.start_date,
            end_date=job_master.end_date
        )

        return JobPostingAnalyzeResponse(
            job_posting_id=job_post.job_post_id,
            is_existing=is_existing,
            company_name=company.name,
            job_title=job_master.job_title,
            main_responsibilities=job_master.main_tasks if isinstance(job_master.main_tasks, list) else [],
            required_skills=dto.skills,
            recruitment_status=job_master.status,
            recruitment_period=recruitment_period,
            ai_summary=job_master.ai_summary or ""
        )

    async def _process_new_content(
        self, url: str, extracted_data: Any, fingerprint: str
    ) -> JobPostingAnalyzeResponse:
        """완전히 새로운 채용 공고를 처리합니다 (신규 JobMaster + JobPost 생성)"""

        logger.info("🆕 Processing completely new job posting.")

        # TODO: 1. Company 생성 또는 조회
        # TODO: 2. JobMaster 생성
        # TODO: 3. Skills 매칭 및 연결
        # TODO: 4. JobPost 생성
        # TODO: 5. Response 반환

        raise NotImplementedError("_process_new_content is not yet implemented")