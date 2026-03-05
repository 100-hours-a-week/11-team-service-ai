import asyncio
import logging
import json
from unittest.mock import MagicMock

from pipelines.resume_analysis.infrastructure.adapters.llm.ai_agent.resercher_graph.graph import TechResearcher
from pipelines.resume_analysis.infrastructure.adapters.llm.ai_agent.configuration import AnalyseContext
from pipelines.resume_analysis.domain.models.job import JobInfo, EvaluationCriteria
from pipelines.resume_analysis.domain.models.document import DocumentType

async def main():
    # 로그 레벨을 INFO로 설정해 node.py 내부의 logger.info 메시지를 콘솔에 출력
    logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
    
    print("=" * 50)
    print("🚀 TechResearcher 모의 실행 스크립트")
    print("=" * 50)
    
    # 그래프 인스턴스 생성
    researcher = TechResearcher()
    
    config = {
        "configurable": {
            "model_provider": "vllm",
            "model_name": "Qwen/Qwen3-8B-AWQ",
        }
    }

    # Mock 데이터 생성
    job_info = JobInfo(
        company_name="카카오(Kakao)",
        main_tasks=[
            "대규모 언어 모델(LLM)을 활용한 AI 에이전트 파이프라인 설계 및 구현",
            "LangChain, LlamaIndex, LangGraph 등을 활용한 RAG 및 복잡한 워크플로우 개발",
            "vLLM, TensorRT-LLM 등을 이용한 오픈소스 LLM 분산 인퍼런스 시스템 구축 및 최적화",
            "Vector DB를 활용한 대규모 문서 기반 검색 및 추천 시스템 구축"
        ],
        tech_stacks=[
            "Python", "PyTorch", "LangChain", "LangGraph", "LlamaIndex", 
            "vLLM", "TensorRT", "FAISS", "Milvus", "Qdrant", "Docker", "Kubernetes", "FastAPI"
        ],
        summary="최신 LLM 기술과 Agentic Workflow를 활용하여 새로운 AI 서비스를 개척할 AI 엔지니어를 모십니다. 단순 API 호출을 넘어, 추론 최적화 및 복잡한 아키텍처 설계 경험이 있는 분을 환영합니다.",
        evaluation_criteria=[
            EvaluationCriteria(name="Agentic 워크플로우 및 RAG 설계", description="LangGraph, LangChain 등을 활용해 복잡한 AI 에이전트 시스템 및 RAG 구조를 설계하고 성능을 개선한 경험"),
            EvaluationCriteria(name="인퍼런스/서빙 최적화", description="vLLM, TensorRT-LLM 등을 활용하여 모델 추론 속도 향상 및 GPU 메모리 최적화를 이뤄낸 경험"),
            EvaluationCriteria(name="AI 퀄리티 문제 해결", description="환각(Hallucination) 제어, 프롬프트 엔지니어링, 혹은 파라미터 미세조정(PEFT/QLoRA)을 통한 품질 개선 경험")
        ]
    )
    
    doc_type = DocumentType.RESUME
    document_text = "안녕하세요, 4년 차 AI 엔지니어입니다. 이전 직장에서 LangGraph와 FastAPI를 연동해 멀티 에이전트 기반 RAG 시스템을 구축했습니다. 검색 정확도를 향상시키기 위해 Milvus 벡터 DB와 BM25를 결합한 Hybrid Search를 도입했고, 자체 서비스용 LLM은 vLLM 서버로 띄워 PagedAttention 방식으로 GPU 메모리 오작동 없이 동시 접속을 효율적으로 처리한 경험이 있습니다. 또한 모델의 도메인 특화 성능을 높이기 위해 QLoRA로 Llama-3 모델을 미세조정한 경험도 보유하고 있습니다."

    context_data = AnalyseContext(
        job_info=job_info, doc_type=doc_type, doc_text=document_text
    )

    
    # 에이전트 실행 대기
    result = await researcher.start_researcher(
        config=config, 
        runtime=context_data
    )
    
    print("\n" + "=" * 50)
    print("✅ 최종 상태 (ResearcherState) 결과 출력")
    print("=" * 50)
    
    # Pydantic 기반 모델(TechInfo, TechCompetencyFactor) 직렬화를 위한 헬퍼 함수
    def custom_serializer(obj):
        if hasattr(obj, 'model_dump'):
            return obj.model_dump()
        return str(obj)

    # JSON 이쁘게 포맷팅해서 출력
    print(json.dumps(result, indent=2, default=custom_serializer, ensure_ascii=False))

    # 앱/테스트 스크립트 종료 전, 메모리 누수 방지를 위해 Weaviate 공용 클라이언트를 정석적으로 닫아줌
    try:
        from shared.vector_db.client import WeaviateConnectionManager
        WeaviateConnectionManager.close()
    except Exception as e:
        logging.error(f"Weaviate 클라이언트 종료 중 에러: {e}")

if __name__ == "__main__":
    # 비동기 시작점
    asyncio.run(main())
