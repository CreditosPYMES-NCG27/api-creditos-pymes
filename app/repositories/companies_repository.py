from typing import Sequence, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import desc, func, select

from app.models.company import Company


class CompanyRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, company: Company) -> Company:
        self.session.add(company)
        await self.session.commit()
        await self.session.refresh(company)
        return company

    async def update(self, company_id: UUID, update_data: dict) -> Company | None:
        # Get the table model for updating
        result = await self.session.execute(
            select(Company).where(Company.id == company_id)
        )
        company = result.scalars().first()
        if not company:
            return None
        for key, value in update_data.items():
            setattr(company, key, value)
        await self.session.commit()
        await self.session.refresh(company)
        return company

    async def get_by_id(self, company_id: UUID) -> Company | None:
        result = await self.session.execute(
            select(Company).where(Company.id == company_id)
        )
        company = result.scalars().first()
        return company

    async def get_by_tax_id(self, tax_id: str) -> Company | None:
        result = await self.session.execute(
            select(Company).where(Company.tax_id == tax_id)
        )
        company = result.scalars().first()
        return company

    async def get_by_user_id(self, user_id: UUID) -> Company | None:
        result = await self.session.execute(
            select(Company).where(Company.user_id == user_id)
        )
        company = result.scalars().first()
        return company

    async def list(
        self,
        *,
        page: int,
        limit: int,
        sort: str | None,
        order: str,
    ) -> Tuple[Sequence[Company], int]:
        offset = (page - 1) * limit
        query = select(Company)

        if sort:
            col = getattr(Company, sort, None)
            if col is not None:
                query = query.order_by(col.asc() if order == "asc" else col.desc())

        else:
            query = query.order_by(desc(Company.created_at))

        total = (
            await self.session.execute(select(func.count()).select_from(Company))
        ).scalar_one()

        items = (
            (await self.session.execute(query.offset(offset).limit(limit)))
            .scalars()
            .all()
        )

        return items, total
