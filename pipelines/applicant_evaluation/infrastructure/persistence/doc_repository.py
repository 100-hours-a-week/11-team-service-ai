from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import NoResultFound

from ai.shared.db.model.models import (
    JobApplication, ApplicationDocument, ApplicationDocumentParsed, FileObject
)
from ...domain.interface.repository_interfaces import DocRepository
from ...domain.models.document import ApplicantDocuments, ParsedDoc, FileInfo

class SqlAlchemyDocRepository(DocRepository):
    """
    지원 서류 관련 데이터 조회 및 저장을 담당하는 Repository 구현체
    """
    def __init__(self, session: Session):
        self.session = session

    def get_documents(self, user_id: int, job_id: int) -> ApplicantDocuments:
        # 1. 지원 내역(JobApplication) 조회
        # 문서(parsed 포함)와 파일 정보를 한 번에 로딩
        application = (
            self.session.query(JobApplication)
            .filter(
                JobApplication.user_id == user_id,
                JobApplication.job_master_id == job_id
            )
            .one_or_none()
        )

        if not application:
            # 지원 내역조차 없으면 빈 객체 반환 (비즈니스 로직에 따라 에러 처리 가능)
            return ApplicantDocuments()

        # 2. 문서 목록 조회 (JobApplication ID 기준)
        docs = (
            self.session.query(ApplicationDocument)
            .options(
                joinedload(ApplicationDocument.file),    # 파일 메타데이터 로딩
                joinedload(ApplicationDocument.parsed)   # 파싱 결과 로딩
            )
            .filter(ApplicationDocument.job_application_id == application.job_application_id)
            .all()
        )

        # 3. 도메인 객체 조립 (Aggregating)
        agg = ApplicantDocuments()

        for doc in docs:
            # A. FileInfo 변환
            # 주의: file_path는 S3 key 등을 조합해서 만들어야 할 수 있음. 
            # 여기서는 FileObject.object_key를 path로 사용한다고 가정.
            if not doc.file:
                continue

            f_info = FileInfo(
                file_path=doc.file.object_key,
                file_type=doc.doc_type
            )

            # B. ParsedDoc 변환
            p_doc = None
            # backref="parsed"는 리스트라서 첫 번째 요소를 가져오거나, 1:1 관계 설정에 따라 다름.
            # models.py 정의상 'parsed'는 backref list일 가능성이 높음 (기본 설정).
            # 하지만 1:1 논리이므로 첫 번째 것을 사용.
            parsed_record = doc.parsed[0] if doc.parsed else None
            
            if parsed_record:
                p_doc = ParsedDoc(
                    doc_type=doc.doc_type,
                    text=parsed_record.raw_text,
                    is_valid=(parsed_record.parsing_status == 'SUCCESS')
                )

            # C. 타입별 할당
            if doc.doc_type == "RESUME":
                agg.resume_file = f_info
                agg.parsed_resume = p_doc
            elif doc.doc_type == "PORTFOLIO":
                agg.portfolio_file = f_info
                agg.parsed_portfolio = p_doc

        return agg

    def save_parsed_doc(
        self, 
        user_id: int, 
        job_id: int, 
        parsed_doc: ParsedDoc
    ) -> None:
        # 1. 대상 문서 행(ApplicationDocument) 찾기
        # (지원내역 -> 문서 테이블 조인)
        target_doc = (
            self.session.query(ApplicationDocument)
            .join(JobApplication, ApplicationDocument.job_application_id == JobApplication.job_application_id)
            .filter(
                JobApplication.user_id == user_id,
                JobApplication.job_master_id == job_id,
                ApplicationDocument.doc_type == parsed_doc.doc_type
            )
            .one_or_none()
        )

        if not target_doc:
            raise NoResultFound(f"Document record not found for user={user_id}, job={job_id}, type={parsed_doc.doc_type}")

        # 2. 파싱 데이터 저장 (Upsert Logic)
        # 이미 파싱 데이터가 있는지 확인
        existing_parsed = (
            self.session.query(ApplicationDocumentParsed)
            .filter(ApplicationDocumentParsed.application_document_id == target_doc.application_document_id)
            .one_or_none()
        )

        if existing_parsed:
            # Update (필요하다면)
            existing_parsed.raw_text = parsed_doc.text
            existing_parsed.parsing_status = "SUCCESS" if parsed_doc.is_valid else "FAILED"
        else:
            # Insert
            new_parsed = ApplicationDocumentParsed(
                application_document_id=target_doc.application_document_id,
                raw_text=parsed_doc.text,
                parsing_status="SUCCESS" if parsed_doc.is_valid else "FAILED"
            )
            self.session.add(new_parsed)
        
        # 주의: commit()은 Service Layer나 Transaction 관리자가 호출하는 것이 원칙이나, 
        # 단순함을 위해 여기서 flush 할 수 있음. 여기서는 session에만 담아둠.
        self.session.flush()
