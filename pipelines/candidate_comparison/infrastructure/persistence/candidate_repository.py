from typing import Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from ...domain.interface.repository_interfaces import CandidateRepository
from ...domain.models.candidate import (
    Candidate,
    ApplicantDocuments,
    EvaluationResult,
    CompetencyScore,
)
from shared.db.model.models import (
    JobApplication,
    ApplicationDocument,
    AiApplicantEvaluation,
)


class SqlAlchemyCandidateRepository(CandidateRepository):
    """
    지원자 애그리거트 저장소 구현체 (Async)

    조회 데이터:
    - JobApplication (지원 내역)
    - ApplicationDocument + ApplicationDocumentParsed (서류)
    - AiApplicantEvaluation (평가 결과)
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_candidate(
        self, candidate_id: str, job_posting_id: str
    ) -> Optional[Candidate]:
        """
        지원자 애그리거트 조회

        Args:
            candidate_id: 지원자 ID
            job_posting_id: 공고 ID

        Returns:
            Candidate: 서류 + 평가 결과를 포함한 애그리거트
        """
        user_id = int(candidate_id)
        job_master_id = int(job_posting_id)
        # 1. JobApplication 조회
        app_stmt = select(JobApplication).where(
            JobApplication.user_id == user_id,
            JobApplication.job_master_id == job_master_id,
        )
        app_result = await self.session.execute(app_stmt)
        application = app_result.scalars().first()

        if not application:
            return None

        job_application_id = int(application.job_application_id)  # type: ignore

        # 2. 서류 조회 (이력서 + 포트폴리오)
        documents = await self._get_documents(job_application_id)

        # 3. 평가 결과 조회
        evaluation = await self._get_evaluation(job_application_id)

        if not evaluation:
            # 평가 결과가 없으면 None 반환
            return None

        # 4. Candidate 애그리거트 생성
        return Candidate(documents=documents, evaluation=evaluation)

    async def _get_documents(self, job_application_id: int) -> ApplicantDocuments:
        """
        지원자의 서류(이력서 + 포트폴리오) 조회

        Args:
            job_application_id: 지원 내역 ID

        Returns:
            ApplicantDocuments: 파싱된 서류 텍스트
        """
        # ApplicationDocument 조회 (이력서, 포트폴리오)
        doc_stmt = (
            select(ApplicationDocument)
            .options(joinedload(ApplicationDocument.parsed))
            .where(
                ApplicationDocument.job_application_id == job_application_id,
            )
        )
        doc_result = await self.session.execute(doc_stmt)
        docs = doc_result.scalars().unique().all()

        parsed_resume: Optional[str] = None
        parsed_portfolio: Optional[str] = None

        for doc in docs:
            # parsed는 List[ApplicationDocumentParsed]
            parsed_list = doc.parsed if doc.parsed else []  # type: ignore
            if not parsed_list:
                continue

            parsed_record = parsed_list[0]
            raw_text = str(parsed_record.raw_text) if parsed_record.raw_text else None

            if doc.doc_type == "RESUME":
                parsed_resume = raw_text
            elif doc.doc_type == "PORTFOLIO":
                parsed_portfolio = raw_text

        return ApplicantDocuments(
            parsed_resume=parsed_resume or "",
            parsed_portfolio=parsed_portfolio,
        )

    async def _get_evaluation(
        self, job_application_id: int
    ) -> Optional[EvaluationResult]:
        """
        AI 평가 결과 조회

        Args:
            job_application_id: 지원 내역 ID

        Returns:
            EvaluationResult: 역량 점수 + 리뷰
        """
        # AiApplicantEvaluation 조회
        eval_stmt = select(AiApplicantEvaluation).where(
            AiApplicantEvaluation.job_application_id == job_application_id
        )
        eval_result = await self.session.execute(eval_stmt)
        evaluation = eval_result.scalars().first()

        if not evaluation:
            return None

        # comparison_scores JSON 파싱 → CompetencyScore 리스트
        competency_scores = self._parse_competency_scores(
            evaluation.comparison_scores  # type: ignore
        )

        return EvaluationResult(
            competency_scores=competency_scores,
            one_line_review=str(evaluation.one_line_review or ""),
            feedback_detail=str(evaluation.feedback_detail or ""),
        )

    def _parse_competency_scores(
        self, comparison_scores_json: Any
    ) -> list[CompetencyScore]:
        """
        JSON 역량 점수를 CompetencyScore 리스트로 변환

        comparison_scores JSON 구조:
        [
            {"name": "기술 스택", "score": 85, "feedback": "Good"},
            {"name": "경험", "score": 72, "feedback": "OK"}
        ]

        Args:
            comparison_scores_json: DB에 저장된 JSON 데이터

        Returns:
            list[CompetencyScore]: 역량 점수 리스트
        """
        if not comparison_scores_json:
            return []

        if not isinstance(comparison_scores_json, list):
            return []

        scores = []
        for item in comparison_scores_json:
            if isinstance(item, dict):
                scores.append(
                    CompetencyScore(
                        name=item.get("name", "Unknown"),
                        score=float(item.get("score", 0)),
                        feedback=item.get("description", ""),
                    )
                )

        return scores
