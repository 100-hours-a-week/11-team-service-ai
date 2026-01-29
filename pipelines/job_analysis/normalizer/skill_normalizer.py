"""Skill Name Normalization Logic"""
import logging
import asyncio
from typing import Optional, List

from datetime import datetime
from weaviate.classes.query import MetadataQuery
from job_analysis.data.models import Skill
from job_analysis.data.vector_repository.skill_vector_repo import SkillVectorRepository
from job_analysis.utils.ai_agent import get_ai_agent

logger = logging.getLogger(__name__)

SKILL_COLLECTION = "Skill"


class SkillNormalizer:
    """스킬 정규화 처리 클래스"""

    # 유사도 임계값
    HIGH_SIMILARITY_THRESHOLD = 0.85
    MEDIUM_SIMILARITY_THRESHOLD = 0.40

    def __init__(self, repo=None):
        """
        Args:
            repo: SkillRepository (Service에서 주입)
        """
        self.vector_repo = SkillVectorRepository()
        self.repo = repo

    async def get_or_create(self, raw_skill_name: str) -> int:
        """스킬 ID를 반환하거나 불가능할 경우 새로 생성합니다."""
        # 1. ID 조회
        skill_id = await self.find_id(raw_skill_name)
        if skill_id:
            return skill_id

        # 2. 신규 생성
        logger.info(f"🆕 Creating new skill via Normalizer: {raw_skill_name}")
        
        new_skill = Skill(
            skill_name=raw_skill_name,
            category=None,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        saved_skill = await self.repo.create(new_skill)

        # 3. Vector DB 등록        
        try:
            await self.vector_repo.add_skill(saved_skill.skill_id, saved_skill.skill_name)
            logger.info(f"✅ Added new skill to Vector DB: {saved_skill.skill_name}")
        except Exception as e:
            logger.error(f"❌ Failed to add new skill to Vector DB: {e}")
            
        return saved_skill.skill_id

    async def get_or_create_batch(self, raw_skill_names: List[str]) -> List[int]:
        """여러 스킬의 ID를 보장합니다. (병렬 처리)"""
        if not raw_skill_names:
            return []

        # SQLAlchemy AsyncSession은 동시성(Concurrent) 쓰기를 지원하지 않음
        # 따라서 asyncio.gather 대신 순차적으로 실행해야 함
        skill_ids = []
        for name in raw_skill_names:
            skill_id = await self.get_or_create(name)
            skill_ids.append(skill_id)
            
        return skill_ids

    async def find_id(self, raw_skill_name: str) -> Optional[int]:
        """
        스킬명을 분석하여 기존 스킬 ID를 찾습니다.

        Flow:
        1. RDB Alias 조회
        2. Vector DB 조회
           - HIGH: 즉시 반환
           - MEDIUM: AI 판단
           - LOW: None
        """
        logger.debug(f"🔍 Normalizing skill name: {raw_skill_name}")

        # 1. RDB Alias 조회
        if self.repo:
            alias = await self.repo.find_alias_by_name(raw_skill_name)
            if alias:
                logger.debug(f"✅ Found exact match in Alias: {raw_skill_name} -> ID: {alias.skill_id}")
                return alias.skill_id

        # 2. 벡터 DB 검색 (전처리된 이름 사용)
        similar_skills = await self.vector_repo.search_similar(raw_skill_name, limit=1)

        if not similar_skills:
            logger.debug(f"📝 No similar skills found in Vector DB.")
            return None

        # 4. 유사도 기반 판단
        best_match = similar_skills[0]
        similarity = best_match["similarity_score"]
        skill_id = best_match["skill_id"]
        normalized_name = best_match["name"]

        if similarity >= self.HIGH_SIMILARITY_THRESHOLD:
            logger.debug(f"✅ High similarity match: {normalized_name} (score: {similarity:.2f}) -> ID: {skill_id}")

            # [Validation] RDB에 실제로 존재하는지 확인
            if self.repo:
                exists = await self.repo.find_by_id(skill_id)
                if not exists:
                     logger.warning(f"⚠️ Skill ID {skill_id} found in VectorDB but missing in RDB. Treating as new.")
                     return None

            # [Self-Learning] 이름이 완전히 똑같지 않다면 별칭으로 등록
            if best_match["name"] != raw_skill_name:
                await self._learn_new_alias(skill_id, raw_skill_name, normalized_name)

            return skill_id

        elif similarity >= self.MEDIUM_SIMILARITY_THRESHOLD:
            logger.info(f"⚠️ Medium similarity match: {normalized_name} (score: {similarity:.2f}). Asking Agent...")

            # AI 판단 요청
            ai_agent = get_ai_agent()
            is_same = await ai_agent.is_same_skill(raw_skill_name, normalized_name)
            if is_same:
                # [Validation] RDB에 실제로 존재하는지 확인
                if self.repo:
                    exists = await self.repo.find_by_id(skill_id)
                    if not exists:
                         logger.warning(f"⚠️ Skill ID {skill_id} found in VectorDB but missing in RDB. Treating as new.")
                         return None

                logger.info(f"✅ Agent confirmed match. Using ID: {skill_id}")
                await self._learn_new_alias(skill_id, raw_skill_name, normalized_name)
                return skill_id
            else:
                logger.info(f"❌ Agent denied match. Treating as new skill.")
                return None

        else:
            logger.debug(f"📝 Low similarity ({similarity:.2f}). New skill.")
            return None

    async def _learn_new_alias(self, skill_id: int, raw_name: str, normalized_name: str):
        """새로운 별칭을 학습합니다 (RDB & Vector DB)."""
        if not self.repo:
            return

        # RDB Alias 추가
        try:
            # 트랜잭션의 Savepoint를 생성하여, 에러 발생 시 이 블록만 롤백하고 전체 세션은 유지합니다.
            async with self.repo.session.begin_nested():
                await self.repo.add_alias(skill_id, raw_name)
            logger.info(f"📚 Learned new alias (RDB): {raw_name} -> ID {skill_id}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to add alias to RDB: {e}")

        # Vector DB 추가
        try:
            await self.vector_repo.add_skill(skill_id, raw_name)
            logger.info(f"📚 Learned new alias (Vector): {raw_name}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to add alias to Vector DB: {e}")
