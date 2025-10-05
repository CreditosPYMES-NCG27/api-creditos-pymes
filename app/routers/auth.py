from fastapi import APIRouter, Depends, HTTPException
from supabase import AsyncClient

from app.dependencies import supabase_for_user
from app.models.user import UserWithCompany
from app.services.user_service import UserService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me", response_model=UserWithCompany)
async def get_current_user(
    supa: AsyncClient = Depends(supabase_for_user),
):
    """
    Obtener información extendida del usuario autenticado.

    Este endpoint:
    - Valida el JWT token automáticamente (supabase_for_user)
    - Obtiene el user_id del contexto JWT (get_current_user_id)
    - Consulta datos del usuario desde la BD a través del servicio
    - Incluye información básica de la empresa si existe
    """
    service = UserService(supa)
    profile = await service.get_current_user_profile()

    if not profile:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return profile
