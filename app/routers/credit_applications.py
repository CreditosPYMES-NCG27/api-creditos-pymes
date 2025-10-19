from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.enums import CreditApplicationStatus
from app.dependencies.auth import CurrentUserDep
from app.dependencies.services import CreditApplicationServiceDep
from app.schemas.credit_application import (
    CreditApplicationCreate,
    CreditApplicationResponse,
    CreditApplicationUpdate,
)
from app.schemas.pagination import Paginated, PaginatedParams, pagination_params

router = APIRouter(prefix="/credit-applications", tags=["credit-applications"])

# Campos permitidos para ordenamiento
ALLOWED_SORT_FIELDS = {
    "id",
    "requested_amount",
    "term_months",
    "status",
    "risk_score",
    "approved_amount",
    "interest_rate",
    "created_at",
    "updated_at",
}


@router.get("/", response_model=Paginated[CreditApplicationResponse])
async def list_credit_applications(
    service: CreditApplicationServiceDep,
    user: CurrentUserDep,
    params: PaginatedParams = Depends(pagination_params),
    status: CreditApplicationStatus | None = Query(
        None, description="Filtrar por estado de la solicitud"
    ),
    company_id: UUID | None = Query(None, description="Filtrar por ID de compañía"),
):
    """Listar solicitudes de crédito con paginación y filtros opcionales.

    - Los solicitantes solo pueden ver sus propias solicitudes.
    - Los operadores y administradores pueden ver todas las solicitudes.
    - Filtros opcionales: status, company_id
    - Campos permitidos para ordenamiento: id, requested_amount, term_months, status,
      risk_score, approved_amount, interest_rate, created_at, updated_at
    """
    # Sanitizar el campo de ordenamiento
    if params.sort and params.sort not in ALLOWED_SORT_FIELDS:
        raise HTTPException(
            status_code=400,
            detail=f"Campo de ordenamiento no permitido: {params.sort}. "
            f"Campos permitidos: {', '.join(sorted(ALLOWED_SORT_FIELDS))}",
        )

    return await service.list_applications(
        user,
        page=params.page,
        limit=params.limit,
        status=status,
        company_id=company_id,
        sort=params.sort,
        order=params.order,
    )


@router.post("/", response_model=CreditApplicationResponse)
async def create_credit_application(
    service: CreditApplicationServiceDep,
    application: CreditApplicationCreate,
    user: CurrentUserDep,
):
    """Crear una nueva solicitud de crédito (solo solicitantes)."""
    return await service.create_application(application, user)


@router.get("/{application_id}", response_model=CreditApplicationResponse)
async def get_credit_application(
    service: CreditApplicationServiceDep,
    application_id: UUID,
    user: CurrentUserDep,
):
    """Obtener una solicitud de crédito por su ID.

    - Los solicitantes solo pueden ver sus propias solicitudes.
    - Los operadores y administradores pueden ver todas las solicitudes.
    """
    return await service.get_application_by_id(application_id, user)


@router.patch("/{application_id}", response_model=CreditApplicationResponse)
async def update_credit_application(
    service: CreditApplicationServiceDep,
    application_id: UUID,
    application: CreditApplicationUpdate,
    user: CurrentUserDep,
):
    """Actualizar parcialmente una solicitud de crédito (solo operadores)."""
    return await service.update_application(user, application_id, application)
