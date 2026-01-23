from typing import Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from job_analysis.data.models import Company, CompanyAlias


class CompanyRepository:
    """Company 테이블 전용 Repository (CRUD)"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, company: Company) -> Company:
        """새로운 회사를 저장합니다."""
        self.session.add(company)
        # Service 레벨에서 Transaction을 관리하도록 commit 제거
        await self.session.flush() 
        return company

    async def find_by_id(self, company_id: int) -> Optional[Company]:
        """ID로 회사를 조회합니다."""
        stmt = select(Company).where(Company.company_id == company_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def find_by_name(self, name: str) -> Optional[Company]:
        """이름으로 회사를 조회합니다."""
        stmt = select(Company).where(Company.name == name).where(Company.deleted_at.is_(None))
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def update(self, company: Company) -> Company:
        """회사 정보를 업데이트합니다."""
        await self.session.commit()
        await self.session.refresh(company)
        return company

    async def find_alias_by_name(self, raw_name: str) -> Optional[CompanyAlias]:
        """별칭(Alias)으로 회사를 조회합니다."""
        # 1. Company 테이블에서 정확히 일치하는 이름 검색
        stmt = select(Company).where(Company.name == raw_name).where(Company.deleted_at.is_(None))
        result = await self.session.execute(stmt)
        company = result.scalars().first()
        
        if company:
            # Company 테이블에 있으면 가상의 Alias 객체로 반환 (호환성 위해)
            # 주의: 실제 DB에는 없지만 로직상 Alias처럼 처리
            return CompanyAlias(
                company_id=company.company_id,
                alias_name=company.name,
                alias_normalized=company.name
            )

        # 2. CompanyAlias 테이블 검색
        stmt = select(CompanyAlias).where(CompanyAlias.alias_name == raw_name).where(CompanyAlias.deleted_at.is_(None))
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def add_alias(self, company_id: int, raw_name: str) -> CompanyAlias:
        """기존 회사에 새로운 별칭을 추가합니다."""
        alias = CompanyAlias(
            company_id=company_id,
            source='ai_learning',
            alias_name=raw_name,
            alias_normalized=raw_name.strip().lower(), # 간단한 정규화
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        self.session.add(alias)
        self.session.add(alias)
        await self.session.flush()
        return alias
