from typing import List
from ..dtos import PipelineEvaluateResponse
from ...domain.models.document import ParsedDoc
from ...domain.models.evaluation import CompetencyResult
from ...domain.models.report import AnalysisReport
from ...domain.interface.repository_interfaces import (
    JobRepository, DocRepository, ReportRepository
)
from ...domain.interface.adapter_interfaces import (
    FileStorage, TextExtractor, AnalystAgent
)
# 만약 도메인 예외가 필요하면 import
# from ...domain.exceptions import DocumentNotFoundError, JobNotFoundError

class ApplicationAnalyzer:
    """
    지원자 분석 파이프라인을 조율하는 애플리케이션 서비스
    (도메인 로직 직접 수행 X, 순서 제어 O)
    """
    def __init__(
        self,
        job_repo: JobRepository,
        doc_repo: DocRepository,
        report_repo: ReportRepository,
        file_storage: FileStorage,
        extractor: TextExtractor,
        agent: AnalystAgent
    ):
        self.job_repo = job_repo
        self.doc_repo = doc_repo
        self.report_repo = report_repo
        self.file_storage = file_storage
        self.extractor = extractor
        self.agent = agent

    def run(self, user_id: int, job_id: int) -> PipelineEvaluateResponse:
        # 1. 채용 공고 정보 조회
        job_info = self.job_repo.get_job_info(job_id)
        if not job_info:
            raise ValueError(f"Job not found: {job_id}") # 또는 도메인 예외 Raise

        # 2. 지원자 서류 상태 조회 (Aggregate Root)
        documents = self.doc_repo.get_documents(user_id, job_id)
        
        # 3. 서류 전처리 (분석 가능한 텍스트가 없으면 추출 수행)
        if not documents.is_ready_for_analysis():
            self._prepare_documents(user_id, job_id, documents)
            # 상태 갱신 (선택적: 다시 조회하거나, _prepare 안에서 객체 업데이트)
            # 여기서는 documents 객체를 직접 업데이트했다고 가정하거나, 다시 조회
            documents = self.doc_repo.get_documents(user_id, job_id)
            
            if not documents.is_ready_for_analysis():
                 raise ValueError("Document preparation failed.")

        resume_text = documents.parsed_resume.text
        portfolio_text = documents.parsed_portfolio.text if documents.parsed_portfolio else ""

        # 4. 개별 역량 평가 (AI 호출 Loop)
        competency_results: List[CompetencyResult] = []
        for criteria in job_info.evaluation_criteria:
            result = self.agent.evaluate_competency(
                job_info=job_info,
                criteria=criteria,
                resume_text=resume_text,
                portfolio_text=portfolio_text
            )
            competency_results.append(result)

        # 5. 종합 평가 및 리포트 생성 (AI Synthesis -> Domain Factory)
        overall_feedback = self.agent.synthesize_report(job_info, competency_results)
        
        report = AnalysisReport.create(
            job_info=job_info,
            results=competency_results,
            feedback=overall_feedback
        )

        # 6. 결과 저장
        self.report_repo.save_report(user_id, job_id, report)

        # 7. 응답 반환 (DTO 변환)
        return PipelineEvaluateResponse.from_domain(report)

    def _prepare_documents(self, user_id: int, job_id: int, documents):
        """텍스트 추출이 필요한 문서들을 처리하여 저장소에 저장하는 헬퍼 메서드"""
        # 도메인 모델에게 "무슨 파일이 분석 준비 안 됐어?" 라고 물어봄
        missing_types = documents.get_missing_parsed_types() # 예: ["RESUME", "PORTFOLIO"]
        
        for doc_type in missing_types:
            file_info = documents.resume_file if doc_type == "RESUME" else documents.portfolio_file
            
            if not file_info:
                # 원본 파일조차 없으면 스킵하거나 에러 (비즈니스 규칙에 따름)
                continue
                
            # A. S3에서 다운로드
            file_content = self.file_storage.download_file(file_info.file_path)
            
            # B. 텍스트 추출 (Infrastructure Adapter)
            text = self.extractor.extract_text(file_content)
            
            # C. ParsedDoc 생성 및 저장
            parsed_doc = ParsedDoc(doc_type=doc_type, text=text)
            self.doc_repo.save_parsed_doc(user_id, job_id, doc_type, parsed_doc)
