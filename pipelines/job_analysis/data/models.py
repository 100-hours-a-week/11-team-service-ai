from datetime import date, datetime
from typing import Optional, Any
from sqlalchemy import (
    String,
    Date,
    DateTime,
    ForeignKey,
    BigInteger,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.mysql import JSON

from shared.db.connection import Base


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    profile_image_file_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, nullable=True
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    nickname: Mapped[str] = mapped_column(String(30), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class Company(Base):
    __tablename__ = "companies"

    company_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    domain: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class CompanyAlias(Base):
    __tablename__ = "company_aliases"
    __table_args__ = (
        UniqueConstraint(
            "company_id", "alias_normalized", name="uk_company_aliases_company_norm"
        ),
    )

    alias_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    company_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("companies.company_id"), nullable=False, index=True
    )
    source: Mapped[str] = mapped_column(String(30), nullable=False)
    alias_name: Mapped[str] = mapped_column(String(150), nullable=False)
    alias_normalized: Mapped[str] = mapped_column(String(150), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class Skill(Base):
    __tablename__ = "skills"

    skill_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    skill_name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class SkillAlias(Base):
    __tablename__ = "skill_aliases"
    __table_args__ = (
        UniqueConstraint(
            "skill_id", "alias_normalized", name="uk_skill_aliases_skill_norm"
        ),
    )

    alias_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    skill_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("skills.skill_id"), nullable=False, index=True
    )
    alias_name: Mapped[str] = mapped_column(String(100), nullable=False)
    alias_normalized: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class JobMasterSkill(Base):
    __tablename__ = "job_master_skills"

    job_master_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("job_masters.job_master_id"), primary_key=True
    )
    skill_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("skills.skill_id"), primary_key=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class JobMaster(Base):
    __tablename__ = "job_masters"
    # ... (기존 내용 유지)

    # Primary Key
    job_master_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )

    # Foreign Key
    company_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("companies.company_id"), nullable=False, index=True
    )

    # Core Fields
    job_title: Mapped[str] = mapped_column(String(150), nullable=False)
    main_tasks: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)

    # AI Analysis Fields
    ai_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    evaluation_criteria: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)

    # Status & Dates
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Audit Fields
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class JobPost(Base):
    __tablename__ = "job_posts"

    # Primary Key
    job_post_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )

    # Foreign Keys
    job_master_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("job_masters.job_master_id"), nullable=False, index=True
    )
    company_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("companies.company_id"), nullable=False, index=True
    )
    created_by: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("users.user_id"), nullable=True, index=True
    )

    # Core Fields
    source_type: Mapped[str] = mapped_column(String(20), nullable=False)
    source_url: Mapped[str] = mapped_column(String(500), nullable=False, unique=True)
    source_url_hash: Mapped[str] = mapped_column(String(64), nullable=False)  # CHAR(64)

    # Optional Fields
    raw_company_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    raw_job_title: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)

    # JSON Field
    main_tasks: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)

    # Status Fields
    recruitment_status: Mapped[str] = mapped_column(String(20), nullable=False)
    registration_status: Mapped[str] = mapped_column(String(20), nullable=False)

    # Date Fields
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Audit Fields
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Fingerprint
    fingerprint_hash: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )  # CHAR(64)
    ai_job_id: Mapped[int] = mapped_column(
        BigInteger, nullable=True
    )  # Temporary fix for missing column mapping
