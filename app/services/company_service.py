from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import UserRole
from app.core.errors import NotFoundError, ValidationDomainError
from app.repositories.companies_repository import CompanyRepository
from app.repositories.protocols import (
    CompanyRepositoryProtocol,
    ProfileRepositoryProtocol,
)
from app.schemas.auth import Principal
from app.schemas.company import CompanyResponse, CompanyUpdate
from app.schemas.pagination import Paginated, PaginatedParams
from app.services.base_service import BaseService


class CompanyService(BaseService):
    """Servicio para lógica de negocio de empresas"""

    def __init__(
        self,
        session: AsyncSession,
        company_repo: CompanyRepositoryProtocol | None = None,
        profile_repo: ProfileRepositoryProtocol | None = None,
    ):
        super().__init__(session, profile_repo)
        self.company_repo = company_repo or CompanyRepository(session)

    async def get_company_by_id(
        self, user: Principal, company_id: UUID
    ) -> CompanyResponse:
        await self.assert_role(user.sub, UserRole.admin, UserRole.operator)
        company = await self.company_repo.get_by_id(company_id)
        if not company:
            raise NotFoundError("Empresa no encontrada")
        return CompanyResponse.model_validate(company.model_dump())

    async def get_company_by_user_id(self, user: Principal) -> CompanyResponse:
        company = await self.company_repo.get_by_user_id(UUID(user.sub))
        if not company:
            raise NotFoundError("Empresa no encontrada para el usuario dado")
        return CompanyResponse.model_validate(company.model_dump())

    async def update_user_company(
        self,
        user: Principal,
        company: CompanyUpdate,
    ) -> CompanyResponse:
        existing = await self.company_repo.get_by_user_id(UUID(user.sub))
        if not existing:
            raise NotFoundError("Empresa no encontrada para el usuario dado")

        update_data = {k: v for k, v in company.model_dump().items() if v is not None}
        if not update_data:
            raise ValidationDomainError("No hay datos para actualizar")

        updated = await self.company_repo.update(existing.id, update_data)
        if not updated:
            raise ValidationDomainError("Error al actualizar datos de la empresa")
        return CompanyResponse.model_validate(updated.model_dump())

    async def list_companies(
        self,
        user: Principal,
        params: PaginatedParams,
    ) -> Paginated[CompanyResponse]:
        await self.assert_role(user.sub, UserRole.admin, UserRole.operator)
        items, total = await self.company_repo.list(
            page=params.page,
            limit=params.limit,
            sort=params.sort,
            order=params.order,
        )
        meta = BaseService.create_pagination_meta(
            total=total,
            page=params.page,
            per_page=params.limit,
        )
        return Paginated[CompanyResponse](
            items=[CompanyResponse.model_validate(item.model_dump()) for item in items],
            meta=meta,
        )
