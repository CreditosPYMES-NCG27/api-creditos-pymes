from uuid import UUID

from fastapi import APIRouter, Depends

from app.dependencies.auth import CurrentUserDep
from app.dependencies.services import CompanyServiceDep
from app.schemas.company import CompanyResponse, CompanyUpdate
from app.schemas.pagination import Paginated, PaginatedParams, pagination_params

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("/me", response_model=CompanyResponse)
async def read_my_company(
    service: CompanyServiceDep,
    user: CurrentUserDep,
):
    """Devuelve la empresa asociada al usuario autenticado."""
    return await service.get_company_by_user_id(user)


@router.patch("/me", response_model=CompanyResponse)
async def update_my_company(
    service: CompanyServiceDep,
    company: CompanyUpdate,
    user: CurrentUserDep,
):
    """Actualiza parcialmente los datos de la empresa asociada al usuario autenticado."""
    return await service.update_user_company(user, company)


@router.get("/{company_id}", response_model=CompanyResponse)
async def read_company(
    service: CompanyServiceDep,
    company_id: UUID,
    user: CurrentUserDep,
):
    """Devuelve una empresa por su ID (solo administradores y operadores)."""
    return await service.get_company_by_id(user, company_id)


@router.get("/", response_model=Paginated[CompanyResponse])
async def list_companies(
    service: CompanyServiceDep,
    user: CurrentUserDep,
    params: PaginatedParams = Depends(pagination_params),
):
    """Lista todas las empresas con paginación (solo administradores y operadores)."""
    return await service.list_companies(user, params)
