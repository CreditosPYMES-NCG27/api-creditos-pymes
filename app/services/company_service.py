from typing import List
from uuid import UUID

from supabase import AsyncClient

from app.repositories.companies_repository import CompanyRepository
from app.schemas.company import CompanyCreate, CompanyResponse, CompanyUpdate


class CompanyService:
    """Servicio para lógica de negocio de empresas"""

    def __init__(self, supabase_client: AsyncClient):
        self.repo = CompanyRepository(supabase_client)

    async def list_companies(
        self,
        page: int = 1,
        limit: int = 20,
        status: str | None = None,
        search: str | None = None,
    ) -> List[CompanyResponse]:
        companies = await self.repo.list_companies(
            page=page, limit=limit, status=status, search=search
        )
        return [CompanyResponse(**company) for company in companies]

    async def create_company(
        self, company: CompanyCreate, user_id: str
    ) -> CompanyResponse:
        if await self.repo.check_user_has_company(user_id):
            raise ValueError("El usuario ya tiene una empresa registrada")

        if await self.repo.check_company_exists_by_tax_id(company.tax_id):
            raise ValueError("El tax_id ya está registrado")

        data = company.model_dump()
        data["user_id"] = user_id

        created_company = await self.repo.create_company(data)
        # No actualizar company_id en profiles - la relación es unidireccional desde companies

        return CompanyResponse(**created_company)

    async def get_company_by_id(self, company_id: UUID) -> CompanyResponse:
        company = await self.repo.get_company_by_id(company_id)
        return CompanyResponse(**company)

    async def update_company(
        self, company_id: UUID, company: CompanyUpdate, user_id: str
    ) -> CompanyResponse:
        existing = await self.repo.get_company_by_id(company_id)
        if existing["user_id"] != user_id:
            raise ValueError("No tienes permisos para actualizar esta empresa")

        update_data = {k: v for k, v in company.model_dump().items() if v is not None}
        if not update_data:
            raise ValueError("No se proporcionaron campos para actualizar")

        if "tax_id" in update_data and await self.repo.check_company_exists_by_tax_id(
            update_data["tax_id"], company_id
        ):
            raise ValueError("El tax_id ya está registrado")

        updated = await self.repo.update_company(company_id, update_data)
        return CompanyResponse(**updated)

    async def get_company_by_user_id(self, user_id: str) -> CompanyResponse | None:
        company = await self.repo.get_company_by_user_id(user_id)
        return CompanyResponse(**company) if company else None
