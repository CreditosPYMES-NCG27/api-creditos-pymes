from typing import Sequence, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, desc, func, select

from app.core.enums import CreditApplicationStatus
from app.models.credit_application import CreditApplication


class CreditApplicationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_applications(
        self,
        *,
        page: int = 1,
        limit: int = 20,
        status: CreditApplicationStatus | None = None,
        company_id: UUID | None = None,
        sort: str | None = None,
        order: str = "desc",
    ) -> Tuple[Sequence[CreditApplication], int]:
        offset = (page - 1) * limit
        query = select(CreditApplication)

        if status:
            query = query.where(CreditApplication.status == status)
        if company_id:
            query = query.where(CreditApplication.company_id == company_id)

        if sort:
            sort_column = col(getattr(CreditApplication, sort, None))
            if sort_column is not None:
                query = query.order_by(
                    sort_column.asc() if order == "asc" else sort_column.desc()
                )
        else:
            query = query.order_by(desc(CreditApplication.created_at))

        # Count total records matching the filters
        count_query = select(func.count(col(CreditApplication.id))).select_from(
            CreditApplication
        )

        if status:
            count_query = count_query.where(CreditApplication.status == status)
        if company_id:
            count_query = count_query.where(CreditApplication.company_id == company_id)

        total = (await self.session.execute(count_query)).scalar_one()

        items = (
            (await self.session.execute(query.offset(offset).limit(limit)))
            .scalars()
            .all()
        )

        return items, total

    async def create_application(
        self, application: CreditApplication
    ) -> CreditApplication:
        self.session.add(application)
        await self.session.commit()
        await self.session.refresh(application)
        return application

    async def get_application_by_id(
        self, application_id: UUID
    ) -> CreditApplication | None:
        result = await self.session.execute(
            select(CreditApplication).where(CreditApplication.id == application_id)
        )
        application = result.scalars().first()
        return application

    async def update_application(
        self, application_id: UUID, update_data: dict
    ) -> CreditApplication | None:
        result = await self.session.execute(
            select(CreditApplication).where(CreditApplication.id == application_id)
        )
        application = result.scalars().first()
        if not application:
            return None
        for key, value in update_data.items():
            setattr(application, key, value)
        await self.session.commit()
        await self.session.refresh(application)
        return application

    async def check_company_has_pending_application(self, company_id: UUID) -> bool:
        result = await self.session.execute(
            select(CreditApplication).where(
                CreditApplication.company_id == company_id,
                CreditApplication.status == CreditApplicationStatus.pending,
            )
        )
        return result.scalars().first() is not None
