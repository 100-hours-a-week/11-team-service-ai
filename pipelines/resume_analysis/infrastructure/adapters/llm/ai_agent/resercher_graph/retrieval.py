from contextlib import contextmanager
from typing import Iterator

import weaviate
from langchain_openai import OpenAIEmbeddings
from langchain_weaviate import WeaviateVectorStore
from pydantic import SecretStr

from shared.config import settings

WEAVIATE_HOST = settings.WEAVIATE_HOST
WEAVIATE_PORT = settings.WEAVIATE_PORT
WEAVIATE_GRPC_PORT = settings.WEAVIATE_GRPC_PORT


# 임베딩 모델 생성
def get_embeddings_model() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(
        model=settings.EMBEDDING_MODEL,
        api_key=SecretStr(settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None,
        chunk_size=200,
    )


@contextmanager
def make_weaviate_store() -> Iterator[WeaviateVectorStore]:
    # Connect to Weaviate and create a retriever
    with weaviate.connect_to_local(
        host=WEAVIATE_HOST,
        port=WEAVIATE_PORT,
        grpc_port=WEAVIATE_GRPC_PORT,
        skip_init_checks=True,
    ) as weaviate_client:

        store = WeaviateVectorStore(
            client=weaviate_client,
            index_name="TECH_DOCUMENT",
            text_key="text",
            embedding=get_embeddings_model(),
            attributes=["query", "url", "title", "created_at"],
        )
        yield store

        # # 명시적으로 검색 옵션을 정의합니다. (예: k=4 (4개 반환), return_uuids=True (UUID 포함))
        # search_kwargs = {"k": 4}
        # yield store.as_retriever(search_kwargs=search_kwargs)
