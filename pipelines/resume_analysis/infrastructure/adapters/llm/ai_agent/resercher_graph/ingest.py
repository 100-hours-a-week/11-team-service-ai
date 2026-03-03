# from langchain_core.embeddings import Embeddings
# from langchain_openai import OpenAIEmbeddings
# from shared.config import settings

# def get_embeddings_model() -> Embeddings:
#     return OpenAIEmbeddings(model="text-embedding-3-small", chunk_size=200)

# def ingest_docs():
#     text_splitter = RecursiveCharacterTextSplitter(chunk_size=4000, chunk_overlap=200)
#     embedding = get_embeddings_model()

#     with weaviate.connect_to_local(
#         host = settings.WEAVIATE_HOST,
#         port = settings.WEAVIATE_PORT,
#         grpc_port = settings.WEAVIATE_GRPC_PORT,
#         skip_init_checks=True
#     ) as weaviate_client:
#         # General Guides and Tutorials
#         general_guides_and_tutorials_vectorstore = WeaviateVectorStore(
#             client=weaviate_client,
#             index_name=WEAVIATE_GENERAL_GUIDES_AND_TUTORIALS_INDEX_NAME,
#             text_key="text",
#             embedding=embedding,
#             # Weaviate에 쿼리 시 반환할 메타데이터 속성 지정, 따라서 Ducument 저장시에 해당 속성이 반드시 포함되어야 함
#             attributes=["source", "title"],
#         )

#         # 어떤 문서가 이미 벡터 저장소에 저장되었는지 기록하는 역활을 함 (중복 인덱싱 방지)
#         record_manager = SQLRecordManager(
#             namespace=f"weaviate/{WEAVIATE_GENERAL_GUIDES_AND_TUTORIALS_INDEX_NAME}",
#             db_url=RECORD_MANAGER_DB_URL,
#         )
#         record_manager.create_schema()
        
#         # general_guides_and_tutorials_docs = ingest_general_guides_and_tutorials()
#         general_guides_and_tutorials_docs = load_single_url("https://m.sports.naver.com/kbaseball/article/022/0004086120")
#         # general_guides_and_tutorials_docs = load_notion_docs("/Users/haram/Desktop/카카오부캠/코드/rag-base/test/sample_data/test")

#         # 문서 분할
#         docs_transformed = text_splitter.split_documents(
#             general_guides_and_tutorials_docs
#         )
#         # 필터링: 너무 짧은 문서는 제외
#         docs_transformed = [
#             doc for doc in docs_transformed if len(doc.page_content) > 10
#         ]

#         # weaviate에서 검색을 할 때 metadata의 source, title 필드를 포함하여 반환하도록 설정했으므로 문서에도 해당 필드가 반드시 포함되어야 함
#         for doc in docs_transformed:
#             if "source" not in doc.metadata:
#                 doc.metadata["source"] = ""
#             if "title" not in doc.metadata:
#                 doc.metadata["title"] = ""
#         indexing_stats = index(
#             docs_transformed,
#             record_manager,
#             general_guides_and_tutorials_vectorstore,
#             cleanup="full",
#             # 벡터db의 metadata에 포함된 source 필드를 고유 식별자로 사용, record_manager에서는 group_id컬럼에 식별자를 저장하여 중복 인덱싱 방지
#             # 만약 source_id_key를 사용하지 않는다면 page_content의 해시값이 고유 식별자로 사용됨
#             # 문서가 조금만 바껴도 해시값이 달라지기 때문에 동일 문서임에도 불구하고 중복 인덱싱될 수 있음, 따라서 source와 같은 고유 식별자를 사용하는 것이 좋음
#             source_id_key="source",
#             force_update=(os.environ.get("FORCE_UPDATE") or "false").lower() == "true",
#         )
#         logger.info(f"Indexing stats: {indexing_stats}")
#         num_vecs = (
#             weaviate_client.collections.get(
#                 WEAVIATE_GENERAL_GUIDES_AND_TUTORIALS_INDEX_NAME
#             )
#             .aggregate.over_all()
#             .total_count
#         )
#         logger.info(
#             f"General Guides and Tutorials now has this many vectors: {num_vecs}",
#         )