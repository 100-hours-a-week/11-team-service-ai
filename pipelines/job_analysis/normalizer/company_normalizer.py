"""Company Name Normalization Logic"""
import logging
from typing import Optional

from weaviate.classes.query import MetadataQuery
from datetime import datetime
from job_analysis.data.models import Company
from job_analysis.data.vector_repository.company_vector_repo import CompanyVectorRepository
from job_analysis.utils.ai_agent import get_ai_agent

logger = logging.getLogger(__name__)

COMPANY_COLLECTION = "Company"


class CompanyNormalizer:
    """회사명 정규화 처리 클래스"""

    # 유사도 임계값
    HIGH_SIMILARITY_THRESHOLD = 0.85
    MEDIUM_SIMILARITY_THRESHOLD = 0.50

    def __init__(self, repo=None):
        """
        Args:
            repo: CompanyRepository (Service에서 주입)
        """
        self.vector_repo = CompanyVectorRepository()
        self.repo = repo

    async def get_or_create(self, raw_company_name: str) -> int:
        """
        회사 ID를 반환하거나 불가능할 경우 새로 생성합니다. (Get or Create)
        """
        # 1. ID 조회 (Find) - rdb alias + vector db를 통한 유사도 조회 및 alias 학습
        company_id = await self.find_id(raw_company_name)
        if company_id:
            return company_id

        # 2. 신규 생성 (Create) - rdb + vector db를 통한 유사도 조회 결과가 없을 경우
        logger.info(f"🆕 Creating new company via Normalizer: {raw_company_name}")
        
        new_company = Company(
            name=raw_company_name,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        saved_company = await self.repo.create(new_company)

        # 3. Vector DB 등록 (검색용)
        try:
            await self.vector_repo.add_company(saved_company.company_id, saved_company.name)
            logger.info(f"✅ Added new company to Vector DB: {saved_company.name}")
        except Exception as e:
            logger.error(f"❌ Failed to add new company to Vector DB: {e}")

        return saved_company.company_id

    async def find_id(self, raw_company_name: str) -> Optional[int]:
        """
        회사명을 분석하여 기존 회사 ID를 찾습니다.

        Flow:
        1. RDB Alias 조회 (정확 일치)
        2. Vector DB 조회 (유사도 검색)
           - HIGH: 즉시 반환
           - MEDIUM: AI 판단 후 반환
           - LOW: None 반환
        """
        logger.info(f"🔍 Normalizing company name: {raw_company_name}")

        # 1. RDB Alias 조회 (Exact Match)
        if self.repo:
            alias = await self.repo.find_alias_by_name(raw_company_name)
            if alias:
                logger.info(f"✅ Found exact match in Alias: {raw_company_name} -> ID: {alias.company_id}")
                return alias.company_id

        # 2. 벡터 DB 검색 (전처리된 이름 사용)
        similar_companies = await self.vector_repo.search_similar(raw_company_name, limit=1)

        if not similar_companies:
            logger.info(f"📝 No similar companies found in Vector DB.")
            return None

        # 4. 유사도 기반 판단
        best_match = similar_companies[0]
        similarity = best_match["similarity_score"]
        company_id = best_match["company_id"]
        normalized_name = best_match["name"]

        if similarity >= self.HIGH_SIMILARITY_THRESHOLD:
            logger.info(f"✅ High similarity match: {normalized_name} (score: {similarity:.2f}) -> ID: {company_id}")
            
            # [Validation] RDB에 실제로 존재하는지 확인
            if self.repo:
                exists = await self.repo.find_by_id(company_id)
                if not exists:
                        logger.warning(f"⚠️ Company ID {company_id} found in VectorDB but missing in RDB. Treating as new.")
                        return None

            # [Self-Learning] 이름이 완전히 똑같지 않다면 별칭으로 등록
            if best_match["name"] != raw_company_name:
                 await self._learn_new_alias(company_id, raw_company_name)

            return company_id

        elif similarity >= self.MEDIUM_SIMILARITY_THRESHOLD:
            logger.warning(f"⚠️ Medium similarity match: {normalized_name} (score: {similarity:.2f}). Asking Agent...")

            # AI 판단 요청
            ai_agent = get_ai_agent()
            is_same = await ai_agent.is_same_company(raw_company_name, normalized_name)
            
            if is_same:
                # [Validation] RDB에 실제로 존재하는지 확인
                if self.repo:
                    exists = await self.repo.find_by_id(company_id)
                    if not exists:
                         logger.warning(f"⚠️ Company ID {company_id} found in VectorDB but missing in RDB. Treating as new.")
                         return None

                logger.info(f"✅ Agent confirmed match. Using ID: {company_id}")
                await self._learn_new_alias(company_id, raw_company_name)
                return company_id
            else:
                logger.info(f"❌ Agent denied match. Treating as new company.")
                return None

        else:
            logger.info(f"📝 Low similarity ({similarity:.2f}). Treating as new company.")
            return None

    async def _learn_new_alias(self, company_id: int, raw_name: str):
        """새로운 별칭을 학습합니다 (RDB & Vector DB)."""
        if not self.repo:
            return

        # RDB Alias 추가
        try:
            # 트랜잭션의 Savepoint를 생성하여, 에러 발생 시 이 블록만 롤백하고 전체 세션은 유지합니다.
            async with self.repo.session.begin_nested():
                await self.repo.add_alias(company_id, raw_name)
            logger.info(f"📚 Learned new alias (RDB): {raw_name} -> ID {company_id}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to add alias to RDB: {e}")

        # Vector DB 추가
        try:
            await self.vector_repo.add_company(company_id, raw_name)
            logger.info(f"📚 Learned new alias (Vector): {raw_name}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to add alias to Vector DB: {e}")
