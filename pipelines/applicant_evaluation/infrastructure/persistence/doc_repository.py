from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import NoResultFound
import datetime


from shared.db.model.models import (
    JobApplication,
    ApplicationDocument,
    ApplicationDocumentParsed,
)
from ...domain.interface.repository_interfaces import DocRepository
from ...domain.models.document import ApplicantDocuments, ParsedDoc, FileInfo


class SqlAlchemyDocRepository(DocRepository):
    """
    지원 서류 관련 데이터 조회 및 저장을 담당하는 Repository 구현체 (Async)
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_documents(self, user_id: int, job_id: int) -> ApplicantDocuments:
        # 1. 지원 내역(JobApplication) 조회
        stmt = select(JobApplication).where(
            JobApplication.user_id == user_id, JobApplication.job_master_id == job_id
        )
        result = await self.session.execute(stmt)
        application = result.scalars().first()

        if not application:
            return ApplicantDocuments()

        # 2. 문서 목록 조회 (JobApplication ID 기준)
        doc_stmt = (
            select(ApplicationDocument)
            .options(
                joinedload(ApplicationDocument.file),  # 파일 메타데이터 로딩
                joinedload(
                    ApplicationDocument.parsed
                ),  # 파싱 결과 로딩  # type: ignore
            )
            .where(
                ApplicationDocument.job_application_id == application.job_application_id
            )
        )
        doc_result = await self.session.execute(doc_stmt)
        docs = doc_result.scalars().unique().all()  # unique() 권장 (joinedload 사용시)

        # 3. 도메인 객체 조립 (Aggregating)
        agg = ApplicantDocuments()

        for doc in docs:
            # A. FileInfo 변환
            if not doc.file:
                continue

            f_info = FileInfo(
                file_path=str(doc.file.object_key), file_type=str(doc.doc_type)
            )

            # B. ParsedDoc 변환
            p_doc = None
            # parsed가 list인지 단일 객체인지 확인 (Model definition에 따름, 보통 list)
            parsed_list = doc.parsed if doc.parsed else []  # type: ignore
            parsed_record = parsed_list[0] if parsed_list else None

            if parsed_record:
                p_doc = ParsedDoc(
                    doc_type=str(doc.doc_type),
                    text=str(parsed_record.raw_text),
                    is_valid=(str(parsed_record.parsing_status) == "COMPLETED"),
                )

            # C. 타입별 할당
            if doc.doc_type == "RESUME":
                agg.resume_file = f_info
                agg.parsed_resume = p_doc
            elif doc.doc_type == "PORTFOLIO":
                agg.portfolio_file = f_info
                agg.parsed_portfolio = p_doc

        return agg

    async def save_parsed_doc(
        self, user_id: int, job_id: int, parsed_doc: ParsedDoc
    ) -> None:
        # 1. 대상 문서 행(ApplicationDocument) 찾기
        stmt = (
            select(ApplicationDocument)
            .join(
                JobApplication,
                ApplicationDocument.job_application_id
                == JobApplication.job_application_id,
            )
            .where(
                JobApplication.user_id == user_id,
                JobApplication.job_master_id == job_id,
                ApplicationDocument.doc_type == parsed_doc.doc_type,
            )
        )
        result = await self.session.execute(stmt)
        target_doc = result.scalars().first()

        if not target_doc:
            raise NoResultFound(
                f"Document record not found for user={user_id}, job={job_id}, type={parsed_doc.doc_type}"
            )

        # 2. 파싱 데이터 저장 (Upsert Logic)
        parse_stmt = select(ApplicationDocumentParsed).where(
            ApplicationDocumentParsed.application_document_id
            == target_doc.application_document_id
        )
        parse_result = await self.session.execute(parse_stmt)
        existing_parsed = parse_result.scalars().first()

        now = datetime.datetime.now()

        if existing_parsed:
            # Update
            existing_parsed.raw_text = parsed_doc.text  # type: ignore
            existing_parsed.parsing_status = "COMPLETED" if parsed_doc.is_valid else "FAILED"  # type: ignore
            existing_parsed.updated_at = now  # type: ignore
        else:
            # Insert
            new_parsed = ApplicationDocumentParsed(
                application_document_id=target_doc.application_document_id,
                raw_text=parsed_doc.text,
                parsing_status="COMPLETED" if parsed_doc.is_valid else "FAILED",
                created_at=now,
                updated_at=now,
            )
            self.session.add(new_parsed)

        await self.session.flush()
