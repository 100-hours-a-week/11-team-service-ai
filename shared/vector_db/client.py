"""Weaviate Client Configuration and Connection Management"""
import logging
from typing import Optional
import weaviate
from weaviate.classes.init import Auth
from weaviate.client import WeaviateClient

from shared.config import settings

logger = logging.getLogger(__name__)


class WeaviateConnectionManager:
    """Weaviate 연결 관리 클래스 (싱글톤 패턴)"""

    _instance: Optional[WeaviateClient] = None

    @classmethod
    def get_client(cls) -> WeaviateClient:
        """Weaviate 클라이언트를 가져옵니다 (싱글톤)"""
        if cls._instance is None:
            cls._instance = cls._create_client()
        return cls._instance

    @classmethod
    def _create_client(cls) -> WeaviateClient:
        """Weaviate 클라이언트를 생성합니다"""
        try:
            # Weaviate v4 API 사용
            client = weaviate.connect_to_local(
                host=settings.WEAVIATE_HOST,
                port=settings.WEAVIATE_PORT,
                grpc_port=settings.WEAVIATE_GRPC_PORT,
            )

            logger.info(
                f"✅ Connected to Weaviate at {settings.WEAVIATE_HOST}:{settings.WEAVIATE_PORT}"
            )
            return client

        except Exception as e:
            logger.error(f"❌ Failed to connect to Weaviate: {e}")
            raise RuntimeError(f"Weaviate connection failed: {e}")

    @classmethod
    def close(cls):
        """Weaviate 연결을 종료합니다"""
        if cls._instance is not None:
            cls._instance.close()
            cls._instance = None
            logger.info("🔌 Weaviate connection closed")


def get_weaviate_client() -> WeaviateClient:
    """Weaviate 클라이언트를 가져오는 헬퍼 함수"""
    return WeaviateConnectionManager.get_client()
