from typing import List
from uuid import UUID

from supabase import AsyncClient

from app.repositories.companies_repository import CompanyRepository
from app.repositories.credit_applications_repository import CreditApplicationRepository
from app.schemas.credit_application import (
    CreditApplicationCreate,
    CreditApplicationResponse,
    CreditApplicationUpdate,
)


class CreditApplicationService:
    """Servicio para lógica de negocio de aplicaciones de crédito"""

    def __init__(self, supabase_client: AsyncClient):
        self.app_repo = CreditApplicationRepository(supabase_client)
        self.company_repo = CompanyRepository(supabase_client)

    async def list_applications(
        self,
        page: int = 1,
        limit: int = 20,
        status: str | None = None,
        company_id: UUID | None = None,
    ) -> List[CreditApplicationResponse]:
        apps = await self.app_repo.list_applications(
            page=page,
            limit=limit,
            status=status,
            company_id=str(company_id) if company_id is not None else None,
        )
        return [CreditApplicationResponse(**app) for app in apps]

    async def create_application(
        self, application: CreditApplicationCreate, user_id: str
    ) -> CreditApplicationResponse:
        try:
            company = await self.company_repo.get_company_by_user_id(user_id)
        except Exception:
            raise ValueError("Debes registrar una empresa antes de solicitar crédito")

        if await self.app_repo.check_company_has_pending_application(company["id"]):
            raise ValueError("Ya tienes una solicitud pendiente")

        data = application.model_dump(mode="json")
        data["company_id"] = company["id"]

        created = await self.app_repo.create_application(data)
        return CreditApplicationResponse(**created)

    async def get_application_by_id(
        self, application_id: UUID
    ) -> CreditApplicationResponse | None:
        try:
            app = await self.app_repo.get_application_by_id(application_id)
            return CreditApplicationResponse(**app)
        except Exception as e:
            if "no encontrada" in str(e).lower():
                return None
            raise

    async def update_application(
        self, application_id: UUID, application: CreditApplicationUpdate, user_id: str
    ) -> CreditApplicationResponse:
        update_data = {
            k: v for k, v in application.model_dump().items() if v is not None
        }
        if not update_data:
            raise ValueError("No se proporcionaron campos para actualizar")

        updated = await self.app_repo.update_application(application_id, update_data)
        return CreditApplicationResponse(**updated)
