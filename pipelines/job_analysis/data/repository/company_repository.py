from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from job_analysis.data.models import Company


class CompanyRepository:
    """Company 테이블 전용 Repository (CRUD)"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, company: Company) -> Company:
        """새로운 회사를 저장합니다."""
        self.session.add(company)
        await self.session.commit()
        await self.session.refresh(company)
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
