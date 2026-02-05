import asyncio
from typing import List
from shared.schema.applicant import EvaluateResponse
from ...domain.models.document import ParsedDoc
from ...domain.models.evaluation import CompetencyResult
from ...domain.models.report import AnalysisReport
from ...domain.interface.repository_interfaces import JobRepository, DocRepository
from ...domain.interface.adapter_interfaces import (
    FileStorage,
    TextExtractor,
    AnalystAgent,
)


class ApplicationAnalyzer:
    """
    지원자 분석 파이프라인을 조율하는 애플리케이션 서비스 (Async)
    (도메인 로직 직접 수행 X, 순서 제어 O)
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

    async def run(self, user_id: int, job_id: int) -> EvaluateResponse:
        # 1. 채용 공고 정보 조회
        job_info = await self.job_repo.get_job_info(job_id)
        if not job_info:
            raise ValueError(f"Job not found: {job_id}")

        # 2. 지원자 서류 상태 조회 (Aggregate Root)
        documents = await self.doc_repo.get_documents(user_id, job_id)

        # 3. 서류 전처리 (분석 가능한 텍스트가 없으면 추출 수행)
        if not documents.is_ready_for_analysis():
            await self._prepare_documents(user_id, job_id, documents)
            # 상태 갱신
            documents = await self.doc_repo.get_documents(user_id, job_id)

            if not documents.is_ready_for_analysis():
                raise ValueError("Document preparation failed.")

        if not documents.parsed_resume:
            raise ValueError("유저의 서류가 존재하지 않습니다.")
        resume_text = documents.parsed_resume.text
        portfolio_text = (
            documents.parsed_portfolio.text if documents.parsed_portfolio else ""
        )

        # 4. 개별 역량 평가 (AI 호출 Loop -> Parallel)
        # asyncio.gather를 사용하여 병렬 평가 수행
        evaluation_tasks = [
            self.agent.evaluate_competency(
                job_info=job_info,
                criteria=criteria,
                resume_text=resume_text,
                portfolio_text=portfolio_text,
            )
            for criteria in job_info.evaluation_criteria
        ]

        competency_results: List[CompetencyResult] = await asyncio.gather(
            *evaluation_tasks
        )

        # 5. 종합 평가 및 리포트 생성 (AI Synthesis -> Domain Factory)
        overall_feedback = await self.agent.synthesize_report(
            job_info, competency_results
        )

        report = AnalysisReport.create(
            job_info=job_info, results=competency_results, feedback=overall_feedback
        )

        # 6. 응답 반환 (DTO 변환)
        from ..dtos import PipelineEvaluateResponse

        return PipelineEvaluateResponse.from_domain(report)

    async def _prepare_documents(self, user_id: int, job_id: int, documents):
        """텍스트 추출이 필요한 문서들을 처리하여 저장소에 저장하는 헬퍼 메서드 (Async)"""
        missing_types = documents.get_missing_parsed_types()

        for doc_type in missing_types:
            file_info = (
                documents.resume_file
                if doc_type == "RESUME"
                else documents.portfolio_file
            )

            if not file_info:
                continue

            # A. S3에서 다운로드
            file_content = await self.file_storage.download_file(file_info.file_path)

            # B. 텍스트 추출 (Infrastructure Adapter)
            text = await self.extractor.extract_text(file_content)

            # C. ParsedDoc 생성 및 저장
            parsed_doc = ParsedDoc(doc_type=doc_type, text=text)
            # 주의: doc_type 인자가 제거됨 (parsed_doc 안에 포함)
            await self.doc_repo.save_parsed_doc(user_id, job_id, parsed_doc)
