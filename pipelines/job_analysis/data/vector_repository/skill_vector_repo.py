import logging
from weaviate.classes.config import Property, DataType, Configure, VectorDistances
from .base_vector_repo import BaseVectorRepository

logger = logging.getLogger(__name__)


class SkillVectorRepository(BaseVectorRepository):
    """Skill 전용 Vector Repository"""

    COLLECTION_NAME = "Skill"

    def __init__(self):
        super().__init__(self.COLLECTION_NAME)

    def _ensure_collection(self):
        """Skill 컬렉션 스키마 정의 및 생성"""
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
                        Property(
                            name="skill_id",
                            data_type=DataType.INT,
                            description="Database skill ID",
                            skip_vectorization=True,
                        ),
                        Property(
                            name="name",
                            data_type=DataType.TEXT,
                            description="Original skill name",
                        ),
                    ],
                )
                logger.info(f"✅ {self.COLLECTION_NAME} collection created")
        except Exception as e:
            logger.error(f"❌ Failed to ensure {self.COLLECTION_NAME} collection: {e}")
            raise

    async def add_skill(self, skill_id: int, name: str) -> bool:
        """Type-safe wrapper for add"""
        return await self.add(
            {
                "skill_id": skill_id,
                "name": name,
            }
        )
