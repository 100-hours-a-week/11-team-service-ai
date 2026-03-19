import logging
from datetime import date
import uuid
import json
from typing import Any
from pydantic import SecretStr

from shared.config import settings
from shared.vector_db.client import get_weaviate_client

from langchain_openai import OpenAIEmbeddings
from langchain_weaviate import WeaviateVectorStore
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


from langchain_classic.indexes import index
from langchain_classic.indexes import SQLRecordManager

logger = logging.getLogger(__name__)


def get_embeddings_model() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(
        model="text-embedding-3-small",
        api_key=SecretStr(settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None,
        chunk_size=200,
    )


# tavily응답 포맷 : 'query', 'response_time', 'follow_up_questions', 'answer', 'images', 'results', 'request_id'
# results = 'url', 'title', 'content', 'score', 'raw_content'


# 벡터 DB들은 ID 값으로 일반 해시 문자열(sha256 등)이 아닌 반드시 정규 규격의 UUID를 요구합니다. (Not valid 'uuid' 에러 방지)
def custom_uuid_encoder(doc: Document) -> str:
    # 1. 메타데이터를 일관된 형태의 문자열(JSON)로 직렬화 (키 정렬 보장)
    try:
        serialized_meta = json.dumps(doc.metadata, sort_keys=True, ensure_ascii=False)
    except Exception:
        serialized_meta = str(doc.metadata)

    # 2. 문서 본문과 직렬화된 메타데이터를 모두 조합하여 완벽하게 고유한 UUID5 생성
    return str(uuid.uuid5(uuid.NAMESPACE_URL, doc.page_content + serialized_meta))


def ingest_docs(tavilly_response: dict[str, Any]):
    # 1. 문서로드
    results = tavilly_response.get("results", [])
    query = tavilly_response.get("query")
    documents = [
        Document(
            page_content=doc.get("content"),
            metadata={
                "query": query,
                "url": doc.get("url"),
                "title": doc.get("title"),
                "created_at": str(date.today()),
            },
        )
        for doc in results
    ]

    # 2. 청킹 (고도화: 문맥 단절 방지 및 검색 모델 파악에 최적화된 설정)
    # - chunk_size: 글자 수 기준. 1000은 정보가 너무 많아 중요도가 희석될 수 있으므로 핵심만 담기 위해 500으로 축소
    # - chunk_overlap: 잘린 문단 간의 문맥(Context)을 유지하기 위해 오버랩을 50으로 증가
    # - separators: 문장 한가운데가 뚝 끊기는 것을 방지(단락 -> 줄바꿈 -> 마침표/물음표 순으로 쪼갬)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", ". ", "? ", "! ", " ", ""],
    )
    # 문서 분할
    docs_transformed = text_splitter.split_documents(documents)
    # 필터링: 너무 짧은 문서는 제외
    docs_transformed = [doc for doc in docs_transformed if len(doc.page_content) > 10]

    # [에러 수정] 기존 shared.vector_db.connection.get_weaviate_client()는 '싱글톤(하나뿐인)' 객체를 반환
    # 여러 비동기 쓰레드에서 병렬로 ingest_docs를 실행할 때, 한 쓰레드가 with문을 먼저 종료해버리면
    # 전체 Weaviate 클라이언트가 강제로 닫혀버려 다른 쓰레드에서 "WeaviateClient is closed" 에러(일괄 저장 실패)가 발생
    # 따라서 싱글톤을 닫아버리는 with 문 대신, 클라이언트 상태만 검증하고 그대로 재사용하도록 변경하였음
    weaviate_client = get_weaviate_client()
    if not weaviate_client.is_connected():
        weaviate_client.connect()

    # 3. 임베딩 모델 선언
    embedding = get_embeddings_model()

    # 랭체인은 벡터db에 컬렉션이 없는 경우 자동 생성
    vectorstore = WeaviateVectorStore(
        client=weaviate_client,
        index_name="TECH_DOCUMENT",
        text_key="text",
        embedding=embedding,
        attributes=["query", "url", "title", "created_at"],
    )

    # 4. 문서의 중복, 삭제 동기화를 관리하며 문서를 저장
    # 어떤 문서가 이미 벡터 저장소에 저장되었는지 기록하는 역활을 함 (중복 인덱싱 방지)
    record_manager = SQLRecordManager(
        namespace="weaviate/TECH_DOCUMENT",
        db_url="sqlite:///record_manager_cache.sql",
    )
    record_manager.create_schema()

    index(
        docs_transformed,
        record_manager,
        vectorstore,
        cleanup="incremental",
        source_id_key="url",
        key_encoder=custom_uuid_encoder,  # 일반 해시 문자열 대신 벡터DB가 요구하는 유효한 정규 UUID 생성 함수 지정
    )
