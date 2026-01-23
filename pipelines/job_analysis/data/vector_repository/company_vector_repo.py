from weaviate.classes.config import Property, DataType, Configure, VectorDistances
from .base_vector_repo import BaseVectorRepository
import logging

logger = logging.getLogger(__name__)

class CompanyVectorRepository(BaseVectorRepository):
    """Company 전용 Vector Repository"""

    COLLECTION_NAME = "Company"

    def __init__(self):
        super().__init__(self.COLLECTION_NAME)

    def _ensure_collection(self):
        """Company 컬렉션 스키마 정의 및 생성"""
        try:
            if not self.client.collections.exists(self.COLLECTION_NAME):
                logger.info(f"Creating {self.COLLECTION_NAME} collection...")

                self.client.collections.create(
                    name=self.COLLECTION_NAME,
                    vectorizer_config=Configure.Vectorizer.text2vec_openai(
                        model="text-embedding-3-large"
                    ),
                    vector_index_config=Configure.VectorIndex.hnsw(
                        distance_metric=VectorDistances.COSINE
                    ),
                    properties=[
                        Property(name="company_id", data_type=DataType.INT, description="Database company ID", skip_vectorization=True),
                        Property(name="name", data_type=DataType.TEXT, description="Original company name"),
                    ]
                )
                logger.info(f"✅ {self.COLLECTION_NAME} collection created")
        except Exception as e:
            logger.error(f"❌ Failed to ensure {self.COLLECTION_NAME} collection: {e}")
            raise

    async def add_company(self, company_id: int, name: str) -> bool:
        """Type-safe wrapper for add"""
        return await self.add({
            "company_id": company_id,
            "name": name,
        })
