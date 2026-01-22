"""Company Name Normalization Logic"""
import logging
from typing import Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from weaviate.classes.query import MetadataQuery
from shared.vector_db.client import get_weaviate_client

logger = logging.getLogger(__name__)

COMPANY_COLLECTION = "Company"


class SimilarityLevel(Enum):
    """유사도 수준"""
    HIGH = "high"       # 0.85 이상 - 자동 매핑
    MEDIUM = "medium"   # 0.70 ~ 0.84 - 에이전트 판단 필요
    LOW = "low"         # 0.70 미만 - 신규 등록


@dataclass
class CompanyMatchResult:
    """회사명 매칭 결과"""
    company_id: Optional[int]
    company_name: str
    normalized_name: str
    similarity_score: float
    similarity_level: SimilarityLevel
    requires_agent_review: bool


class CompanyNormalizer:
    """회사명 정규화 처리 클래스"""

    # 유사도 임계값
    HIGH_SIMILARITY_THRESHOLD = 0.85
    MEDIUM_SIMILARITY_THRESHOLD = 0.70

    def __init__(self):
        self.client = get_weaviate_client()
        self._ensure_collection()

    def _ensure_collection(self):
        """Company 컬렉션이 존재하는지 확인하고 없으면 생성합니다"""
        try:
            if not self.client.collections.exists(COMPANY_COLLECTION):
                logger.info(f"Creating {COMPANY_COLLECTION} collection...")

                self.client.collections.create(
                    name=COMPANY_COLLECTION,
                    vectorizer_config=None,
                    properties=[
                        {
                            "name": "company_id",
                            "dataType": ["int"],
                            "description": "Database company ID"
                        },
                        {
                            "name": "name",
                            "dataType": ["text"],
                            "description": "Original company name"
                        },
                        {
                            "name": "normalized_name",
                            "dataType": ["text"],
                            "description": "Normalized company name"
                        },
                        {
                            "name": "domain",
                            "dataType": ["text"],
                            "description": "Company domain"
                        }
                    ]
                )
                logger.info(f"✅ {COMPANY_COLLECTION} collection created")

        except Exception as e:
            logger.error(f"❌ Failed to ensure collection: {e}")
            raise

    async def normalize(self, raw_company_name: str) -> CompanyMatchResult:
        """
        회사명을 정규화합니다.

        1. 벡터 DB에서 유사한 회사명 검색
        2. 유사도 수준 판단 (HIGH/MEDIUM/LOW)
        3. 매칭 결과 반환
        """
        logger.info(f"🔍 Normalizing company name: {raw_company_name}")

        # 1. 벡터 DB 검색
        similar_companies = await self._search_similar(raw_company_name, limit=5)

        if not similar_companies:
            # 유사한 회사가 없으면 신규 등록 필요
            logger.info(f"📝 No similar companies found. New registration required.")
            return CompanyMatchResult(
                company_id=None,
                company_name=raw_company_name,
                normalized_name=self._preprocess(raw_company_name),
                similarity_score=0.0,
                similarity_level=SimilarityLevel.LOW,
                requires_agent_review=False
            )

        # 2. 가장 유사한 회사 선택
        best_match = similar_companies[0]
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
            return CompanyMatchResult(
                company_id=best_match["company_id"],
                company_name=best_match["name"],
                normalized_name=best_match["normalized_name"],
                similarity_score=similarity,
                similarity_level=level,
                requires_agent_review=requires_review
            )
        else:
            return CompanyMatchResult(
                company_id=None,
                company_name=raw_company_name,
                normalized_name=self._preprocess(raw_company_name),
                similarity_score=similarity if best_match else 0.0,
                similarity_level=level,
                requires_agent_review=False
            )

    async def _search_similar(self, query: str, limit: int = 5) -> list:
        """벡터 DB에서 유사한 회사 검색"""
        try:
            collection = self.client.collections.get(COMPANY_COLLECTION)

            response = collection.query.near_text(
                query=query,
                limit=limit,
                return_metadata=MetadataQuery(distance=True)
            )

            results = []
            for obj in response.objects:
                similarity = 1.0 - obj.metadata.distance
                results.append({
                    "company_id": obj.properties["company_id"],
                    "name": obj.properties["name"],
                    "normalized_name": obj.properties["normalized_name"],
                    "domain": obj.properties.get("domain", ""),
                    "similarity_score": similarity
                })

            return results

        except Exception as e:
            logger.error(f"❌ Failed to search similar companies: {e}")
            return []

    async def add_to_vector_db(
        self,
        company_id: int,
        name: str,
        normalized_name: str,
        domain: Optional[str] = None
    ) -> bool:
        """벡터 DB에 회사를 추가합니다"""
        try:
            collection = self.client.collections.get(COMPANY_COLLECTION)

            properties = {
                "company_id": company_id,
                "name": name,
                "normalized_name": normalized_name,
                "domain": domain or ""
            }

            collection.data.insert(properties=properties)

            logger.info(f"✅ Added company to vector DB: {name} (ID: {company_id})")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to add company to vector DB: {e}")
            return False

    def _preprocess(self, company_name: str) -> str:
        """회사명 전처리 (정규화)"""
        # 간단한 전처리 예시
        normalized = company_name.strip().lower()

        # 법인 형태 제거 (주식회사, (주), 등)
        normalized = normalized.replace("주식회사", "").replace("(주)", "")
        normalized = normalized.replace("㈜", "").strip()

        return normalized
