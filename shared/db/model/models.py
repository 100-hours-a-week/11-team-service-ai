from sqlalchemy import (
    Column, Integer, String, BigInteger, DateTime, Date, ForeignKey, 
    Text, DECIMAL, JSON, TIMESTAMP
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    user_id = Column(BigInteger, primary_key=True, autoincrement=True)
    platform_name = Column(String(50), nullable=False)  # KAKAO, GOOGLE 등
    email = Column(String(255), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    nickname = Column(String(100), nullable=False)
    img_id = Column(String(50))

class Company(Base):
    __tablename__ = "companies"
    
    company_id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    domain = Column(String(100))
    created_at = Column(DateTime(6), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(6), nullable=False, server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(6))

class JobMaster(Base):
    __tablename__ = "job_masters"
    
    job_master_id = Column(BigInteger, primary_key=True, autoincrement=True)
    company_id = Column(BigInteger, ForeignKey("companies.company_id"), nullable=False)
    job_title = Column(String(150), nullable=False)
    main_tasks = Column(JSON)
    start_date = Column(Date)
    end_date = Column(Date)
    ai_summary = Column(Text)
    evaluation_criteria = Column(JSON)
    status = Column(String(20), nullable=False)
    last_seen_at = Column(DateTime(6))
    created_at = Column(DateTime(6), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(6), nullable=False, server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(6))

    company = relationship("Company")

class Skill(Base):
    __tablename__ = "skills"
    
    skill_id = Column(BigInteger, primary_key=True, autoincrement=True)
    skill_name = Column(String(50), nullable=False, unique=True)
    category = Column(String(50))
    created_at = Column(DateTime(6), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(6), nullable=False, server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(6))

class JobMasterSkill(Base):
    __tablename__ = "job_master_skills"
    
    job_master_id = Column(BigInteger, ForeignKey("job_masters.job_master_id"), primary_key=True)
    skill_id = Column(BigInteger, ForeignKey("skills.skill_id"), primary_key=True)
    created_at = Column(DateTime(6), nullable=False, server_default=func.now())
    deleted_at = Column(DateTime(6))

class JobApplication(Base):
    __tablename__ = "job_applications"
    
    job_application_id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id"), nullable=False)
    job_master_id = Column(BigInteger, ForeignKey("job_masters.job_master_id"), nullable=False)
    status = Column(String(20), nullable=False)
    created_at = Column(DateTime(6), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(6), nullable=False, server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(6))

    user = relationship("User")
    job_master = relationship("JobMaster")

class FileObject(Base):
    __tablename__ = "file_objects"
    
    file_id = Column(BigInteger, primary_key=True, autoincrement=True)
    storage_provider = Column(String(20), nullable=False)
    bucket = Column(String(100))
    object_key = Column(String(500), nullable=False)
    original_name = Column(String(255), nullable=False)
    content_type = Column(String(100))
    size_bytes = Column(BigInteger, nullable=False)
    checksum = Column(String(128))
    created_at = Column(DateTime(6), nullable=False, server_default=func.now())
    deleted_at = Column(DateTime(6))

class ApplicationDocument(Base):
    __tablename__ = "application_documents"
    
    application_document_id = Column(BigInteger, primary_key=True, autoincrement=True)
    job_application_id = Column(BigInteger, ForeignKey("job_applications.job_application_id"), nullable=False)
    file_id = Column(BigInteger, ForeignKey("file_objects.file_id"), nullable=False)
    doc_type = Column(String(20), nullable=False)
    created_at = Column(DateTime(6), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(6), nullable=False, server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(6))

    file = relationship("FileObject")
    application = relationship("JobApplication")

class ApplicationDocumentParsed(Base):
    __tablename__ = "application_document_parsed"
    
    parsed_content_id = Column(BigInteger, primary_key=True, autoincrement=True)
    application_document_id = Column(BigInteger, ForeignKey("application_documents.application_document_id"), nullable=False, unique=True)
    raw_text = Column(Text, nullable=False)
    structured_data = Column(JSON)
    summary = Column(Text)
    parsing_status = Column(String(20), nullable=False)
    model_info = Column(String(50))
    token_count = Column(Integer)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now())

    application_document = relationship("ApplicationDocument", backref="parsed")

class AiApplicantEvaluation(Base):
    __tablename__ = "ai_applicant_evaluation"
    
    evaluation_id = Column(BigInteger, primary_key=True, autoincrement=True)
    job_application_id = Column(BigInteger, ForeignKey("job_applications.job_application_id"), nullable=False, unique=True)
    eval_job_id = Column(BigInteger) # FK constraint to ai_eval_jobs omitted for brevity or needs Model
    final_score = Column(Integer, nullable=False)
    rank_percentile = Column(DECIMAL(5, 2))
    overall_strengths = Column(JSON)
    overall_weaknesses = Column(JSON)
    improvement_suggestions = Column(JSON)
    created_at = Column(DateTime(6), nullable=False, server_default=func.now())

    application = relationship("JobApplication")
