from sqlalchemy.orm import Session
from .infrastructure.persistence.job_repository import SqlAlchemyJobRepository
from .infrastructure.persistence.doc_repository import SqlAlchemyDocRepository
from .infrastructure.persistence.report_repository import SqlAlchemyReportRepository
from .infrastructure.adapters.openai_agent import OpenAiAnalyst
from .infrastructure.adapters.s3_storage import S3FileStorage
from .infrastructure.adapters.pdf_extractor import PyPdfExtractor
from .application.services.analyzer import ApplicationAnalyzer
from .application.dtos import PipelineEvaluateResponse

def run_pipeline(user_id: int, job_id: int) -> PipelineEvaluateResponse:
    """
    지원자 평가 파이프라인의 메인 진입점 (Entrypoint)
    외부(API Router)에서 호출할 때 이 함수를 사용합니다.
    """
    
    # 1. Infrastructure Layer의 구현체 생성 (Dependencies)
    job_repo = SqlAlchemyJobRepository(db_session)
    doc_repo = SqlAlchemyDocRepository(db_session)
    report_repo = SqlAlchemyReportRepository(db_session)
    
    file_storage = S3FileStorage()
    extractor = PyPdfExtractor()
    agent = OpenAiAnalyst()
    
    # 2. Application Layer 서비스에 의존성 주입 (Wiring)
    analyzer = ApplicationAnalyzer(
        job_repo=job_repo,
        doc_repo=doc_repo,
        report_repo=report_repo,
        file_storage=file_storage,
        extractor=extractor,
        agent=agent
    )
    
    # 3. 비즈니스 로직 실행
    result = analyzer.run(user_id, job_id)
    
    return result
