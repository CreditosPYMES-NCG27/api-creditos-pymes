from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from supabase import AsyncClient

from app.dependencies import get_current_user_id, supabase_for_user
from app.schemas.credit_application import (
    CreditApplicationCreate,
    CreditApplicationResponse,
    CreditApplicationUpdate,
)
from app.services.credit_application_service import CreditApplicationService

router = APIRouter(prefix="/credit-applications", tags=["credit-applications"])


def get_credit_application_service(
    supa: AsyncClient = Depends(supabase_for_user),
) -> CreditApplicationService:
    return CreditApplicationService(supa)


@router.get("/", response_model=List[CreditApplicationResponse])
async def list_credit_applications(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: str | None = Query(None, pattern="^(pending|in_review|approved|rejected)$"),
    company_id: UUID | None = Query(None),
    service: CreditApplicationService = Depends(get_credit_application_service),
):
    return await service.list_applications(
        page=page, limit=limit, status=status, company_id=company_id
    )


@router.post("/", response_model=CreditApplicationResponse)
async def create_credit_application(
    application: CreditApplicationCreate,
    user_id: str = Depends(get_current_user_id),
    service: CreditApplicationService = Depends(get_credit_application_service),
):
    try:
        return await service.create_application(application, user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{application_id}", response_model=CreditApplicationResponse)
async def get_credit_application(
    application_id: UUID,
    service: CreditApplicationService = Depends(get_credit_application_service),
):
    application = await service.get_application_by_id(application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    return application


@router.put("/{application_id}", response_model=CreditApplicationResponse)
async def update_credit_application(
    application_id: UUID,
    application: CreditApplicationUpdate,
    user_id: str = Depends(get_current_user_id),
    service: CreditApplicationService = Depends(get_credit_application_service),
):
    try:
        return await service.update_application(application_id, application, user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
