from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from supabase import AsyncClient

from app.dependencies import (
    get_current_user_id,
    supabase_for_user,
)
from app.models.user import UserWithCompany
from app.services.user_service import UserService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me", response_model=UserWithCompany)
async def get_current_user(
    user_id: str = Depends(get_current_user_id),
    supa: AsyncClient = Depends(supabase_for_user),
):
    """
    Obtener perfil completo del usuario autenticado.

    :param user_id: ID del usuario autenticado extraído del token JWT
    :param supa: Cliente de Supabase autenticado con el token JWT
    :return: Perfil completo del usuario autenticado
    :rtype: UserWithCompany
    :raise HTTPException: Si el usuario no es encontrado
    """

    service = UserService(supa)
    profile = await service.get_current_user_profile()

    if not profile:
        raise HTTPException(
            status_code=404,
            detail=f"Usuario {user_id} autenticado pero no encontrado en la base de datos",
        )

    return profile
