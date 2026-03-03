# from contextlib import contextmanager
# from typing import Iterator

# import weaviate
# from langchain_core.embeddings import Embeddings
# from langchain_core.retrievers import BaseRetriever
# from langchain_core.runnables import RunnableConfig
# from langchain_weaviate import WeaviateVectorStore

# from app.rag.configuration import BaseConfiguration
# from app.rag.constants import WEAVIATE_GENERAL_GUIDES_AND_TUTORIALS_INDEX_NAME
# from app.config import settings

# WEAVIATE_HOST = settings.WEAVIATE_HOST
# WEAVIATE_PORT = settings.WEAVIATE_PORT
# WEAVIATE_GRPC_PORT = settings.WEAVIATE_GRPC_PORT

# # 임베딩 모델 생성
# # configuration.embedding_model = "openai/text-embedding-3-small"
# # embedding_model = make_text_encoder(configuration.embedding_model)
# def make_text_encoder(model: str) -> Embeddings:
#     """Connect to the configured text encoder."""
#     provider, model = model.split("/", maxsplit=1)
#     match provider:
#         case "openai":
#             from langchain_openai import OpenAIEmbeddings

#             return OpenAIEmbeddings(model=model)
#         case _:
#             raise ValueError(f"Unsupported embedding provider: {provider}")


# @contextmanager
# def make_weaviate_retriever(
#     configuration: BaseConfiguration, embedding_model: Embeddings
# ) -> Iterator[BaseRetriever]:
    
#     # Connect to Weaviate and create a retriever
#     with weaviate.connect_to_local(
#         host = WEAVIATE_HOST,
#         port = WEAVIATE_PORT,
#         grpc_port = WEAVIATE_GRPC_PORT,
#         skip_init_checks=True
#     ) as weaviate_client:
#         store = WeaviateVectorStore(
#             client=weaviate_client,
#             index_name=WEAVIATE_GENERAL_GUIDES_AND_TUTORIALS_INDEX_NAME,
#             text_key="text",
#             embedding=embedding_model,
#             attributes=["source", "title"],
#         )
#         search_kwargs = {**configuration.search_kwargs, "return_uuids": True}
#         yield store.as_retriever(search_kwargs=search_kwargs)


# # 메인함수
# @contextmanager
# def make_retriever(
#     config: RunnableConfig,
# ) -> Iterator[BaseRetriever]:
#     """Create a retriever for the agent, based on the current configuration."""
#     configuration = BaseConfiguration.from_runnable_config(config)
#     embedding_model = make_text_encoder(configuration.embedding_model)
#     match configuration.retriever_provider:
#         case "weaviate":
#             with make_weaviate_retriever(configuration, embedding_model) as retriever:
#                 yield retriever

#         case _:
#             raise ValueError(
#                 "Unrecognized retriever_provider in configuration. "
#                 f"Expected one of: {', '.join(BaseConfiguration.__annotations__['retriever_provider'].__args__)}\n"
#                 f"Got: {configuration.retriever_provider}"
#             )