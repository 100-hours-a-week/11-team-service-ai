from typing import List, Dict, Any
from weaviate.classes.config import Property, DataType, Configure, VectorDistances
from .base_vector_repo import BaseVectorRepository

JOB_COLLECTION = "JobMaster"

class JobVectorRepository(BaseVectorRepository):
    
    COLLECTION_NAME = "JobMaster"

    def __init__(self):
        super().__init__(self.COLLECTION_NAME)

    def _get_collection_name(self) -> str:
        return self.COLLECTION_NAME

    def _ensure_collection(self):
        """JobMaster 컬렉션 스키마 정의 및 생성"""
        try:
            if not self.client.collections.exists(self.COLLECTION_NAME):
                import logging
                logger = logging.getLogger(__name__)
                
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
                        Property(name="job_master_id", data_type=DataType.INT, description="Job Master ID", skip_vectorization=True),
                        Property(name="job_post_id", data_type=DataType.INT, description="Job Post ID (Specific Posting)", skip_vectorization=True),
                        Property(name="company_id", data_type=DataType.INT, description="Company ID", skip_vectorization=True),
                        Property(name="content", data_type=DataType.TEXT, description="Full Job Data (Serialized JSON) - Embedding Target"),
                    ]
                )
                logger.info(f"✅ {self.COLLECTION_NAME} collection created")
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"❌ Failed to ensure {self.COLLECTION_NAME} collection: {e}")
            raise

    async def search_similar_jobs(self, company_id: int, query_text: str, limit: int = 3) -> List[Dict[str, Any]]:
        """특정 회사 내에서 유사한 공고를 검색합니다."""
        try:
            collection = self.client.collections.get(self.COLLECTION_NAME)
            
            # Weaviate Filter: company_id가 일치하는 데이터만 검색
            from weaviate.classes.query import Filter, MetadataQuery

            response = collection.query.near_text(
                query=query_text,
                limit=limit,
                filters=Filter.by_property("company_id").equal(company_id),
                return_metadata=MetadataQuery(distance=True), # distance 메타데이터 요청
                return_properties=["job_master_id", "content"] # 필요한 필드만 가져옴
            )
            
            results = []
            for obj in response.objects:
                # distance to similarity score (0..1)
                similarity = 1.0 - obj.metadata.distance
                
                results.append({
                    "job_master_id": obj.properties["job_master_id"],
                    "content": obj.properties.get("content"),
                    "similarity": similarity
                })
                
            return results
        except Exception:
            # 컬렉션이 없거나 에러 발생 시 빈 리스트 반환 (안전 장치)
            # logger.error(f"Vector search failed: {e}")
            return []

    async def add_job(self, job_master_id: int, job_post_id: int, company_id: int, content: str):
        """JobMaster 데이터를 Vector DB에 등록합니다."""
        data = {
            "job_master_id": job_master_id,
            "job_post_id": job_post_id,
            "company_id": company_id,
            "content": content
        }
        await self.add(data)

    async def delete_jobs_by_master_id(self, job_master_id: int) -> int:
        """JobMaster ID에 해당하는 모든 벡터 데이터를 삭제합니다."""
        try:
            collection = self.client.collections.get(self.COLLECTION_NAME)
            
            # Weaviate Filter 기반 삭제
            from weaviate.classes.query import Filter
            
            result = collection.data.delete_many(
                where=Filter.by_property("job_master_id").equal(job_master_id)
            )
            # result.successful (int) -> 삭제된 개수
            return result.successful
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"❌ Failed to delete vectors for master id {job_master_id}: {e}")
            return 0


