from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from supabase import AsyncClient

from app.dependencies import get_current_user_id, supabase_for_user
from app.schemas.company import CompanyCreate, CompanyResponse, CompanyUpdate
from app.services.company_service import CompanyService

router = APIRouter(prefix="/companies", tags=["companies"])


def get_company_service(
    supa: AsyncClient = Depends(supabase_for_user),
) -> CompanyService:
    return CompanyService(supa)


@router.get("/", response_model=List[CompanyResponse])
async def list_companies(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: str | None = Query(None, pattern="^(active|inactive|blacklisted)$"),
    search: str | None = Query(None, min_length=1),
    service: CompanyService = Depends(get_company_service),
):
    return await service.list_companies(
        page=page, limit=limit, status=status, search=search
    )


@router.post("/", response_model=CompanyResponse)
async def create_company(
    company: CompanyCreate,
    user_id: str = Depends(get_current_user_id),
    service: CompanyService = Depends(get_company_service),
):
    try:
        return await service.create_company(company, user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(
    company_id: UUID,
    service: CompanyService = Depends(get_company_service),
):
    try:
        return await service.get_company_by_id(company_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: UUID,
    company: CompanyUpdate,
    user_id: str = Depends(get_current_user_id),
    service: CompanyService = Depends(get_company_service),
):
    try:
        return await service.update_company(company_id, company, user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/me", response_model=CompanyResponse)
async def get_my_company(
    user_id: str = Depends(get_current_user_id),
    service: CompanyService = Depends(get_company_service),
):
    company = await service.get_company_by_user_id(user_id)
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    return company
