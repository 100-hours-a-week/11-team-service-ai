"""Skill Name Normalization Logic"""
import logging
from typing import Optional, List
from dataclasses import dataclass
from enum import Enum

from weaviate.classes.query import MetadataQuery
from shared.vector_db.client import get_weaviate_client

logger = logging.getLogger(__name__)

SKILL_COLLECTION = "Skill"


class SimilarityLevel(Enum):
    """유사도 수준"""
    HIGH = "high"       # 0.85 이상 - 자동 매핑
    MEDIUM = "medium"   # 0.70 ~ 0.84 - 에이전트 판단 필요
    LOW = "low"         # 0.70 미만 - 신규 등록


@dataclass
class SkillMatchResult:
    """스킬 매칭 결과"""
    skill_id: Optional[int]
    skill_name: str
    normalized_name: str
    similarity_score: float
    similarity_level: SimilarityLevel
    requires_agent_review: bool
    category: Optional[str] = None


class SkillNormalizer:
    """스킬 정규화 처리 클래스"""

    # 유사도 임계값
    HIGH_SIMILARITY_THRESHOLD = 0.85
    MEDIUM_SIMILARITY_THRESHOLD = 0.70

    def __init__(self):
        self.client = get_weaviate_client()
        self._ensure_collection()

    def _ensure_collection(self):
        """Skill 컬렉션이 존재하는지 확인하고 없으면 생성합니다"""
        try:
            if not self.client.collections.exists(SKILL_COLLECTION):
                logger.info(f"Creating {SKILL_COLLECTION} collection...")

                self.client.collections.create(
                    name=SKILL_COLLECTION,
                    vectorizer_config=None,
                    properties=[
                        {
                            "name": "skill_id",
                            "dataType": ["int"],
                            "description": "Database skill ID"
                        },
                        {
                            "name": "name",
                            "dataType": ["text"],
                            "description": "Original skill name"
                        },
                        {
                            "name": "normalized_name",
                            "dataType": ["text"],
                            "description": "Normalized skill name"
                        },
                        {
                            "name": "category",
                            "dataType": ["text"],
                            "description": "Skill category"
                        }
                    ]
                )
                logger.info(f"✅ {SKILL_COLLECTION} collection created")

        except Exception as e:
            logger.error(f"❌ Failed to ensure collection: {e}")
            raise

    async def normalize(self, raw_skill_name: str) -> SkillMatchResult:
        """
        스킬명을 정규화합니다.

        1. 벡터 DB에서 유사한 스킬명 검색
        2. 유사도 수준 판단 (HIGH/MEDIUM/LOW)
        3. 매칭 결과 반환
        """
        logger.info(f"🔍 Normalizing skill name: {raw_skill_name}")

        # 1. 벡터 DB 검색
        similar_skills = await self._search_similar(raw_skill_name, limit=5)

        if not similar_skills:
            # 유사한 스킬이 없으면 신규 등록 필요
            logger.info(f"📝 No similar skills found. New registration required.")
            return SkillMatchResult(
                skill_id=None,
                skill_name=raw_skill_name,
                normalized_name=self._preprocess(raw_skill_name),
                similarity_score=0.0,
                similarity_level=SimilarityLevel.LOW,
                requires_agent_review=False
            )

        # 2. 가장 유사한 스킬 선택
        best_match = similar_skills[0]
        similarity = best_match["similarity_score"]

        # 3. 유사도 수준 판단
        if similarity >= self.HIGH_SIMILARITY_THRESHOLD:
            level = SimilarityLevel.HIGH
            requires_review = False
            logger.info(f"✅ High similarity match found: {best_match['name']} (score: {similarity:.2f})")

        elif similarity >= self.MEDIUM_SIMILARITY_THRESHOLD:
            level = SimilarityLevel.MEDIUM
            requires_review = True
            logger.warning(f"⚠️ Medium similarity match found: {best_match['name']} (score: {similarity:.2f}). Agent review required.")

        else:
            level = SimilarityLevel.LOW
            requires_review = False
            logger.info(f"📝 Low similarity. New registration required.")
            best_match = None

        # 4. 결과 반환
        if best_match and level != SimilarityLevel.LOW:
            return SkillMatchResult(
                skill_id=best_match["skill_id"],
                skill_name=best_match["name"],
                normalized_name=best_match["normalized_name"],
                similarity_score=similarity,
                similarity_level=level,
                requires_agent_review=requires_review,
                category=best_match.get("category")
            )
        else:
            return SkillMatchResult(
                skill_id=None,
                skill_name=raw_skill_name,
                normalized_name=self._preprocess(raw_skill_name),
                similarity_score=similarity if best_match else 0.0,
                similarity_level=level,
                requires_agent_review=False
            )

    async def normalize_batch(self, raw_skill_names: List[str]) -> List[SkillMatchResult]:
        """여러 스킬을 일괄 정규화합니다"""
        results = []
        for skill_name in raw_skill_names:
            result = await self.normalize(skill_name)
            results.append(result)
        return results

    async def _search_similar(self, query: str, limit: int = 5) -> list:
        """벡터 DB에서 유사한 스킬 검색"""
        try:
            collection = self.client.collections.get(SKILL_COLLECTION)

            response = collection.query.near_text(
                query=query,
                limit=limit,
                return_metadata=MetadataQuery(distance=True)
            )

            results = []
            for obj in response.objects:
                similarity = 1.0 - obj.metadata.distance
                results.append({
                    "skill_id": obj.properties["skill_id"],
                    "name": obj.properties["name"],
                    "normalized_name": obj.properties["normalized_name"],
                    "category": obj.properties.get("category", ""),
                    "similarity_score": similarity
                })

            return results

        except Exception as e:
            logger.error(f"❌ Failed to search similar skills: {e}")
            return []

    async def add_to_vector_db(
        self,
        skill_id: int,
        name: str,
        normalized_name: str,
        category: Optional[str] = None
    ) -> bool:
        """벡터 DB에 스킬을 추가합니다"""
        try:
            collection = self.client.collections.get(SKILL_COLLECTION)

            properties = {
                "skill_id": skill_id,
                "name": name,
                "normalized_name": normalized_name,
                "category": category or ""
            }

            collection.data.insert(properties=properties)

            logger.info(f"✅ Added skill to vector DB: {name} (ID: {skill_id})")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to add skill to vector DB: {e}")
            return False

    def _preprocess(self, skill_name: str) -> str:
        """스킬명 전처리 (정규화)"""
        # 간단한 전처리 예시
        normalized = skill_name.strip().lower()

        # 버전 정보 제거 (선택적)
        # 예: "Python 3.9" -> "python"
        # normalized = re.sub(r'\d+(\.\d+)*', '', normalized).strip()

        return normalized
