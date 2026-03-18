import logging
from tavily import AsyncTavilyClient
from shared.config import settings
from pipelines.resume_analysis.infrastructure.adapters.llm.ai_agent.resercher_graph.ingest import (
    ingest_docs,
)
from pipelines.resume_analysis.infrastructure.adapters.llm.ai_agent.resercher_graph.retrieval import (
    make_weaviate_store,
)

from infinity_client import Client
from langchain_classic.retrievers.contextual_compression import (
    ContextualCompressionRetriever,
)
from langchain_community.document_compressors.infinity_rerank import InfinityRerank

logger = logging.getLogger(__name__)


def pretty_print_docs(docs):
    print(
        f"\n{'-' * 100}\n".join(
            [f"Document {i + 1}:\n\n" + d.page_content for i, d in enumerate(docs)]
        )
    )


async def vector_db_search_node(keyword: str):
    logger.info(f"[{keyword}] 벡터 DB 검색 중...")

    # 1. DB에서 검색 수행
    with make_weaviate_store() as store:
        retriever = store.as_retriever(search_kwargs={"k": 5})

        client = Client(base_url="https://cej3lhbd31z58l-80.proxy.runpod.net")

        compressor = InfinityRerank(client=client, model="BAAI/bge-reranker-large")

        compression_retriever = ContextualCompressionRetriever(
            base_compressor=compressor, base_retriever=retriever
        )

        compressed_docs = await compression_retriever.ainvoke(keyword)

        return compressed_docs


async def test_tavily_search_and_ingest(keyword: str):
    # 1. 비동기 테빌리(Tavily) 클라이언트로 검색
    client = AsyncTavilyClient(api_key=settings.TAVILY_API_KEY)
    try:
        response = await client.search(
            query=keyword,
            search_depth="advanced",
            include_answer=True,
            max_results=3,
        )
    finally:
        await client.close()

    # 결과 로깅
    logger.info(f"Tavily Response Found: {len(response.get('results', []))} results.")

    # 2. 타빌리 검색 결과를 Weaviate 벡터 DB에 청킹 및 인덱싱 (Ingest)동기실행
    ingest_docs(response)


async def main():
    # 1. 문서 검색 및 저장 (Tavily & Weaviate)
    keyword = "카테부 수강생 숫자"

    # 1. 검색 및 임베딩
    # await test_tavily_search_and_ingest(keyword)

    # 2. 벡터 DB 검색 테스트 (미리 저장된 내용 확인)
    search_result = await vector_db_search_node(keyword)

    print("\n--- 최종 검색 결과 ---")
    pretty_print_docs(search_result)


if __name__ == "__main__":
    # 로깅 레벨 등 설정 (콘솔에서 보기 위해)
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    import asyncio

    asyncio.run(main())
