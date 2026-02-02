from typing import List, Dict, Any
import logging
from weaviate.classes.query import MetadataQuery
from shared.vector_db.client import get_weaviate_client

logger = logging.getLogger(__name__)


class BaseVectorRepository:
    """Vector DB 공통 Repository"""

    def __init__(self, collection_name: str):
        self.client = get_weaviate_client()
        self.collection_name = collection_name
        self._ensure_collection()

    def _ensure_collection(self):
        """컬렉션 생성 로직 (하위 클래스에서 구체적으로 구현하거나, 스키마 정의를 주입받도록 설계)"""
        # 공통 초기화 로직이 있다면 여기 작성
        # 실제 컬렉션 생성은 스키마 의존적이므로 각 하위 클래스에서 _create_schema() 호출 등을 통해 수행 권장
        pass

    async def search_similar(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """유사 텍스트 검색 (공통)"""
        try:
            collection = self.client.collections.get(self.collection_name)

            response = collection.query.near_text(
                query=query, limit=limit, return_metadata=MetadataQuery(distance=True)
            )

            results = []
            for obj in response.objects:
                similarity = 1.0 - obj.metadata.distance
                # 기본적으로 모든 프로퍼티를 가져옵니다.
                item = obj.properties.copy()
                item["similarity_score"] = similarity
                results.append(item)

            return results

        except Exception as e:
            logger.error(f"❌ Failed to search in {self.collection_name}: {e}")
            return []

    async def add(self, properties: Dict[str, Any]) -> bool:
        """데이터 추가 (공통)"""
        try:
            collection = self.client.collections.get(self.collection_name)
            collection.data.insert(properties=properties)
            logger.info(f"✅ Added to {self.collection_name} vector DB")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to add to {self.collection_name}: {e}")
            return False
