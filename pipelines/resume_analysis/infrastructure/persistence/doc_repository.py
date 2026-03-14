from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import NoResultFound
from sqlalchemy.dialects.mysql import insert as mysql_insert
import datetime

from ...domain.interface.repository_interfaces import DocRepository
from ...domain.models.document import ApplicantDocument, DocumentType


from shared.db.model.models import (
    JobApplication,
    ApplicationDocument,
    ApplicationDocumentParsed,
)


class SqlAlchemyDocRepository(DocRepository):
    """
    지원 서류 관련 데이터 조회 및 저장을 담당하는 Repository 구현체 (Async)
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_document(
        self, user_id: int, job_id: int, doc_type: str
    ) -> Optional[ApplicantDocument]:
        # 1. 지원 내역(JobApplication) 조회
        stmt = select(JobApplication).where(
            JobApplication.user_id == user_id, JobApplication.job_master_id == job_id
        )
        result = await self.session.execute(stmt)
        application = result.scalars().first()

        if not application:
            return None

        # 2. 특정 문서(ApplicationDocument) 조회 (+ File Meta)
        doc_stmt = (
            select(ApplicationDocument)
            .options(
                joinedload(ApplicationDocument.file),  # 파일 경로
                joinedload(ApplicationDocument.parsed),  # 파싱된 텍스트
            )
            .where(
                ApplicationDocument.job_application_id
                == application.job_application_id,
                ApplicationDocument.doc_type == doc_type,
            )
        )
        doc_result = await self.session.execute(doc_stmt)
        doc = doc_result.scalars().first()

        if not doc:
            return None

        # 3. 도메인 모델(ApplicantDocument) 매핑
        # 3-A. 파일 정보
        file_path = str(doc.file.object_key) if doc.file else None

        # 3-B. 파싱 정보
        parsed_list = doc.parsed if doc.parsed else []  # type: ignore
        parsed_record = parsed_list[0] if parsed_list else None

        extracted_text = None

        if parsed_record:
            extracted_text = str(parsed_record.raw_text)

        return ApplicantDocument(
            doc_type=DocumentType(doc.doc_type),
            file_path=file_path,
            extracted_text=extracted_text,
        )

    async def save_parsed_doc(
        self, user_id: int, job_id: int, document: ApplicantDocument
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
                ApplicationDocument.doc_type == document.doc_type,
            )
        )
        result = await self.session.execute(stmt)
        target_doc = result.scalars().first()

        if not target_doc:
            raise NoResultFound(
                f"Document record not found for user={user_id}, job={job_id}, type={document.doc_type}"
            )

        # 2. 파싱 데이터 저장 (MySQL Upsert Logic)
        now = datetime.datetime.now()

        # 모델의 status 제거 -> 추출 텍스트 존재 여부로 판단
        target_text = document.extracted_text if document.extracted_text else ""
        computed_status = (
            "COMPLETED" if target_text and len(target_text) > 0 else "FAILED"
        )

        insert_stmt = mysql_insert(ApplicationDocumentParsed).values(
            application_document_id=target_doc.application_document_id,
            raw_text=target_text,
            parsing_status=computed_status,
            created_at=now,
            updated_at=now,
        )

        insert_stmt = insert_stmt.on_duplicate_key_update(
            raw_text=insert_stmt.inserted.raw_text,
            parsing_status=insert_stmt.inserted.parsing_status,
            updated_at=insert_stmt.inserted.updated_at,
        )

        await self.session.execute(insert_stmt)

        await self.session.flush()
