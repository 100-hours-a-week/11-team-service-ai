import logging
from typing import Optional
from shared.schema.document import ResumeAnalyzeResponse, PortfolioAnalyzeResponse
from ...domain.models.document import DocumentType
from ...domain.models.report import AnalysisReport
from ...domain.interface.repository_interfaces import JobRepository, DocRepository
from ...domain.interface.adapter_interfaces import (
    FileStorage,
    TextExtractor,
    AnalystAgent,
)
from .mapper import ReportMapper

logger = logging.getLogger(__name__)


class ApplicationAnalyzer:
    """
    지원자 이력서/포트폴리오 분석 파이프라인을 조율하는 애플리케이션 서비스 (Async)
    """

    def __init__(
        self,
        job_repo: JobRepository,
        doc_repo: DocRepository,
        file_storage: FileStorage,
        extractor: TextExtractor,
        agent: AnalystAgent,
    ):
        self.job_repo = job_repo
        self.doc_repo = doc_repo
        self.file_storage = file_storage
        self.extractor = extractor
        self.agent = agent

    async def analyze_resume(
        self, user_id: int, job_id: int
    ) -> ResumeAnalyzeResponse:
        """
        이력서 분석 실행
        """
        report = await self._run_analysis_pipeline(user_id, job_id, DocumentType.RESUME)
        
        logger.info(f"✨ [Resume Analysis Complete] User: {user_id}")
        return ReportMapper.to_resume_response(report)

    async def analyze_portfolio(
        self, user_id: int, job_id: int
    ) -> PortfolioAnalyzeResponse:
        """
        포트폴리오 분석 실행
        """
        report = await self._run_analysis_pipeline(user_id, job_id, DocumentType.PORTFOLIO)
        
        logger.info(f"✨ [Portfolio Analysis Complete] User: {user_id}")
        return ReportMapper.to_portfolio_response(report)

    async def _run_analysis_pipeline(
        self, user_id: int, job_id: int, target_doc_type: DocumentType
    ) -> AnalysisReport:
        """
        공통 분석 파이프라인 로직
        """
        doc_type_str = target_doc_type.value # DB 조회 등에 사용
        
        logger.info(
            f"🚀 [{doc_type_str} Analysis Start] User: {user_id}, Job: {job_id}"
        )

        # 1. 채용 공고 정보 조회
        job_info = await self.job_repo.get_job_info(job_id)
        if not job_info:
            raise ValueError(f"Job not found: {job_id}")

        # 2. 분석 대상 텍스트 준비
        target_text = await self._get_or_extract_text(user_id, job_id, doc_type_str)
        if not target_text:
            raise ValueError(
                f"{doc_type_str} 파일이 존재하지 않거나 텍스트를 추출할 수 없습니다."
            )

        # 3. AI 분석 실행 (LangGraph)
        return await self.agent.run_analysis(
            job_info=job_info,
            document_text=target_text,
            doc_type=target_doc_type,
        )

    async def _get_or_extract_text(
        self, user_id: int, job_id: int, doc_type: str
    ) -> Optional[str]:
        """
        DB에서 파싱된 텍스트 조회, 없으면 파일 다운로드 및 추출 후 저장
        """
        # A. DB 조회
        document = await self.doc_repo.get_document(user_id, job_id, doc_type)
        
        if not document:
             logger.warning(f"Document record not found: User {user_id}, Job {job_id}, Type {doc_type}")
             return None

        # 이미 분석 가능한 텍스트가 있다면 반환
        if document.is_analyzable:
            return document.extracted_text

        # B. 텍스트가 없다면 파일 다운로드 및 추출 시도
        if not document.file_path:
            logger.warning(f"File path missing for document: User {user_id}, Type {doc_type}")
            return None

        try:
            logger.info(f"Downloading file from {document.file_path}...")
            file_content = await self.file_storage.download_file(document.file_path)
            
            logger.info(f"Extracting text from file...")
            text = await self.extractor.extract_text(file_content)
            
            # C. 추출 결과 저장 (상태 업데이트)
            document.update_text(text)
            await self.doc_repo.save_parsed_doc(user_id, job_id, document)
            
            return text
            
        except Exception as e:
            logger.error(f"Failed to extract text for User {user_id}, Type {doc_type}: {e}")
            return None
