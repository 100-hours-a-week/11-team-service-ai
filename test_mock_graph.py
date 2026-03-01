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
            "model_provider": "gemini",
            "model_name": "gemini-flash3",
        }
    }

    # Mock 데이터 생성
    job_info = JobInfo(
        company_name="테스트 기업",
        main_tasks=["웹 프론트엔드 개발", "성능 최적화"],
        tech_stacks=["React", "TypeScript", "Zustand", "Redis"],
        summary="대규모 트래픽을 처리하는 프론트엔드 엔지니어 모십니다.",
        evaluation_criteria=[
            EvaluationCriteria(name="문제해결능력", description="어려운 기술적 문제를 해결한 경험"),
            EvaluationCriteria(name="성능최적화", description="렌더링 최적화 및 로딩 속도 개선 경험"),
        ]
    )
    
    doc_type = DocumentType.RESUME
    document_text = "저는 프론트엔드 개발자입니다. 대규모 트래픽 환경에서 Redis를 이용한 캐싱 도입 경험이 있고, Zustand로 상태 관리를 최적화했습니다."

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

if __name__ == "__main__":
    # 비동기 시작점
    asyncio.run(main())
