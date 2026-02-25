import logging

from candidate_comparison.domain.models.candidate import (
    Candidate,
    ApplicantDocuments,
    EvaluationResult,
    CompetencyScore,
)
from candidate_comparison.domain.models.job import JobInfo
from candidate_comparison.infrastructure.adapters.llm.ai_agent.graph import LLMAnalyst

logger = logging.getLogger(__name__)


async def main():
    """
    LangGraph 기반 지원자 비교 분석 테스트 함수
    """

    # 1. JobInfo 샘플 데이터
    job_info = JobInfo(
        job_posting_id="job-001",
        job_title="백엔드 개발자",
        company_name="테크 컴퍼니",
        main_tasks=[
            "RESTful API 설계 및 개발",
            "데이터베이스 최적화",
            "마이크로서비스 아키텍처 구축",
        ],
        tech_stacks=["Python", "FastAPI", "PostgreSQL", "Docker", "Kubernetes"],
        summary="백엔드 시스템을 설계하고 개발할 수 있는 경력 3년 이상의 개발자를 찾습니다.",
        evaluation_criteria=[
            {"name": "기술 역량", "description": "요구 기술 스택에 대한 실무 경험"},
            {
                "name": "문제 해결 능력",
                "description": "복잡한 시스템 문제를 분석하고 해결한 경험",
            },
            {
                "name": "협업 능력",
                "description": "팀 프로젝트 경험 및 커뮤니케이션 역량",
            },
        ],
    )

    # 2. 내 지원자(my_candidate) 샘플 데이터
    my_candidate = Candidate(
        documents=ApplicantDocuments(
            parsed_resume="이름: 김개발\n경력: 백엔드 개발 4년\n주요 기술: Python, Django, PostgreSQL\n프로젝트: 전자상거래 플랫폼 백엔드 설계 및 개발",
            parsed_portfolio="GitHub: github.com/kimdev\n프로젝트 1: E-commerce API (Django REST Framework)\n프로젝트 2: 실시간 채팅 서버 (FastAPI + WebSocket)",
        ),
        evaluation=EvaluationResult(
            competency_scores=[
                CompetencyScore(
                    name="기술 역량",
                    score=85.0,
                    feedback="Python 및 Django 경험이 풍부함",
                ),
                CompetencyScore(
                    name="문제 해결 능력",
                    score=80.0,
                    feedback="시스템 최적화 경험 보유",
                ),
                CompetencyScore(
                    name="협업 능력", score=75.0, feedback="팀 프로젝트 다수 참여"
                ),
            ],
            one_line_review="탄탄한 백엔드 경험을 보유한 개발자",
            feedback_detail="Django 경험이 많으나 FastAPI 경험은 다소 부족함. 전반적으로 우수한 역량 보유.",
        ),
    )

    # 3. 경쟁 지원자(competitor_candidate) 샘플 데이터
    competitor_candidate = Candidate(
        documents=ApplicantDocuments(
            parsed_resume="이름: 박코딩\n경력: 백엔드 개발 5년\n주요 기술: Python, FastAPI, Docker, Kubernetes\n프로젝트: 마이크로서비스 아키텍처 구축 및 운영",
            parsed_portfolio="GitHub: github.com/parkcoding\n프로젝트 1: MSA 기반 결제 시스템 (FastAPI + K8s)\n프로젝트 2: 대용량 트래픽 처리 서버 설계",
        ),
        evaluation=EvaluationResult(
            competency_scores=[
                CompetencyScore(
                    name="기술 역량",
                    score=90.0,
                    feedback="FastAPI와 K8s 실무 경험 풍부",
                ),
                CompetencyScore(
                    name="문제 해결 능력",
                    score=88.0,
                    feedback="대용량 트래픽 처리 경험 우수",
                ),
                CompetencyScore(
                    name="협업 능력", score=82.0, feedback="MSA 프로젝트에서 리드 경험"
                ),
            ],
            one_line_review="최신 기술 스택에 능숙한 시니어 개발자",
            feedback_detail="FastAPI 및 컨테이너 오케스트레이션 경험이 우수함. 공고 요구사항과 매우 잘 부합.",
        ),
    )

    # 4. LLM 분석 실행
    logger.info("=" * 80)
    logger.info("🚀 Starting LangGraph-based Candidate Comparison Analysis")
    logger.info("=" * 80)

    analyzer = LLMAnalyst(model_name="gemini-3-flash-preview", model_provider="gemini")

    strengths, weaknesses = await analyzer.analyze_candidates(
        my_candidate=my_candidate,
        competitor_candidate=competitor_candidate,
        job_info=job_info,
    )

    # 5. 결과 출력
    logger.info("✅ Analysis Complete")
    logger.info(f"📌 Strengths Report:{strengths}")
    logger.info(f"📌 Weaknesses Report:{weaknesses}")


if __name__ == "__main__":
    import asyncio

    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # main 함수 실행
    asyncio.run(main())
