import weaviate
from weaviate.classes.config import Property, DataType, Configure
from weaviate.classes.query import Filter, MetadataQuery
import logging

from shared.config import settings

logger = logging.getLogger(__name__)


# Weaviate 연결 설정 (로컬 Docker 기준)
try:
    # Weaviate v4 API 사용
    client = weaviate.connect_to_local(
        host=settings.WEAVIATE_HOST,
        port=settings.WEAVIATE_PORT,
        grpc_port=settings.WEAVIATE_GRPC_PORT,
        headers={"X-OpenAI-Api-Key": settings.OPENAI_API_KEY},
    )

    logger.info(
        f"✅ Connected to Weaviate at {settings.WEAVIATE_HOST}:{settings.WEAVIATE_PORT}"
    )
except Exception as e:
    logger.error(f"❌ Failed to connect to Weaviate: {e}")
    raise RuntimeError(f"Weaviate connection failed: {e}")

COLLECTION_NAME = "PracticeCollection"


def setup_collection():
    """컬렉션 생성 (스키마 정의)"""
    if client.collections.exists(COLLECTION_NAME):
        client.collections.delete(COLLECTION_NAME)
        print(f"🗑️ Deleted existing {COLLECTION_NAME}")

    print(f"🔨 Creating {COLLECTION_NAME}...")

    # 1. 텍스트 필드 (content): 임베딩 대상 (검색 가능)
    # 2. 정수 필드 (some_id): 임베딩 제외 (필터링용 메타데이터)
    # 3. 텍스트 필드 (tag): 임베딩 대상 (검색 가능)

    client.collections.create(
        name=COLLECTION_NAME,
        properties=[
            Property(name="content", data_type=DataType.TEXT),
            Property(name="tag", data_type=DataType.TEXT, skip_vectorization=True),
            Property(name="some_id", data_type=DataType.INT, skip_vectorization=True),
        ],
        # V4 방식: 명명된 벡터를 사용하여 벡터화 대상(source_properties)을 명시적으로 제한
        vectorizer_config=[
            Configure.NamedVectors.text2vec_openai(
                name="default",  # 기본 벡터 이름
                source_properties=["content"],  # 오직 'content' 필드만 벡터화 대상!
                vectorize_collection_name=False,
            )
        ],
    )
    print("✅ Collection created!")


def insert_data():
    """데이터 삽입"""
    collection = client.collections.get(COLLECTION_NAME)

    items = [
        {"content": "I love Python programming", "tag": "coding", "some_id": 100},
        {"content": "Bananas are yellow fruits", "tag": "food", "some_id": 200},
        {"content": "React is a frontend library", "tag": "coding", "some_id": 100},
    ]

    with collection.batch.dynamic() as batch:
        for item in items:
            batch.add_object(properties=item)

    print(f"💾 Inserted {len(items)} items.")


def test_search():
    """검색 실험"""
    collection = client.collections.get(COLLECTION_NAME)

    print("\n--- 🔍 Test 1: 'programming' 검색 (텍스트 임베딩 확인) ---")
    response = collection.query.near_text(
        query="programming", limit=2, return_metadata=MetadataQuery(distance=True)
    )
    for obj in response.objects:
        print(f"Found: {obj.properties['content']} (Dist: {obj.metadata.distance:.4f})")

    print("\n--- 🔍 Test 2: '100' 검색 (정수 ID는 임베딩 안 됨 확인) ---")
    # '100'이라는 텍스트로 검색했을 때, ID가 100인 데이터가 '의미적으로' 찾아지지 않아야 함.
    # (단, 우연히 100이라는 텍스트가 content에 있다면 찾아지겠지만 여기선 없음)
    response = collection.query.near_text(
        query="100", limit=1, return_metadata=MetadataQuery(distance=True)
    )
    if not response.objects:
        print("✅ No results found for '100' (As expected, ID is not embedded)")
    else:
        for obj in response.objects:
            print(
                f"Found something: {obj.properties['content']} (Dist: {obj.metadata.distance:.4f})"
            )
            print(
                "=> 만약 결과가 나왔다면, '100'이라는 숫자가 텍스트적으로 해석되어 유사도가 계산된 것임."
            )

    print("\n--- 🔍 Test 3: Filter by ID (메타데이터 역할 확인) ---")
    # some_id가 200인 것만 필터링
    response = collection.query.fetch_objects(
        filters=Filter.by_property("some_id").equal(200), limit=2
    )
    for obj in response.objects:
        print(
            f"Filtered Result: {obj.properties['content']} (ID: {obj.properties['some_id']})"
        )


def check_config():
    """컬렉션 설정 확인"""
    collection = client.collections.get(COLLECTION_NAME)
    config = collection.config.get()

    print("\n--- 🛠 Collection Config Check ---")
    for prop in config.properties:
        print(f"Property: {prop.name}")
        print(f"  - DataType: {prop.data_type}")
        # skip_vectorization 속성 확인 (없으면 False로 간주될 수 있음)
        # Weaviate V4 객체 구조상 vectorizer_config 내부에 있을 수도 있고,
        # prop 객체 자체 속성일 수도 있음. 출력해서 확인.
        if hasattr(prop, "skip_vectorization"):
            print(f"  - Skip Vectorization: {prop.skip_vectorization}")
        else:
            print("  - Skip Vectorization: (Not explicitly set, assuming Default)")

    # 좀 더 확실하게 vector index config 자체를 덤프해볼 수도 있음
    # print(config)


def main():
    try:
        setup_collection()
        insert_data()
        check_config()
        test_search()
    finally:
        client.close()


if __name__ == "__main__":
    main()
