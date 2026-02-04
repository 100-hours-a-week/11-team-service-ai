from typing import Optional
from ....domain.interface.extractor import JobDataExtractor
from ....domain.models.job_data import ExtractedJobData, EvaluationCriteriaItem


class MockJobExtractor(JobDataExtractor):
    """
    테스트 및 개발용 Mock Extractor.
    OpenAI 호출 없이 고정된 더미 데이터를 반환합니다.
    """

    async def extract(self, raw_text: str) -> Optional[ExtractedJobData]:
        return ExtractedJobData(
            company_name="(주)모의기업",
            job_title="백엔드 개발자 (Python/FastAPI)",
            main_tasks=[
                "대규모 트래픽 처리를 위한 백엔드 시스템 설계 및 구현",
                "MSA 기반의 서비스 구축 및 운영",
                "Legacy 시스템 리팩토링 및 성능 최적화",
            ],
            tech_stacks=[
                "Python",
                "FastAPI",
                "Django",
                "AWS",
                "Docker",
                "Kubernetes",
                "MySQL",
            ],
            start_date="2024-01-01",
            end_date="2024-12-31",
            ai_summary="백엔드 개발자를 채용합니다. Python 및 클라우드 환경 경험자를 우대합니다.",
            evaluation_criteria=[
                EvaluationCriteriaItem(
                    name="직무 적합성",
                    description="Python 백엔드 개발 경험 및 아키텍처 이해도",
                ),
                EvaluationCriteriaItem(
                    name="성장 가능성", description="새로운 기술에 대한 학습 의지"
                ),
                EvaluationCriteriaItem(
                    name="문제 해결 능력",
                    description="복잡한 시스템 문제를 논리적으로 해결하는 능력",
                ),
                EvaluationCriteriaItem(
                    name="문화 적합성", description="팀워크 및 커뮤니케이션 능력"
                ),
            ],
        )
