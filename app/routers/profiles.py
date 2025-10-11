from fastapi import (
    APIRouter,
    Depends,
)
from supabase import AsyncClient

from app.dependencies import (
    get_current_user_id,
    supabase_for_user,
)
from app.schemas.profile import UserResponse
from app.services.profile_service import ProfileService

router = APIRouter(prefix="/profiles", tags=["auth"])


def get_profile_service(
    supa: AsyncClient = Depends(supabase_for_user),
) -> ProfileService:
    return ProfileService(supa)


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    user_id: str = Depends(get_current_user_id),
    service: ProfileService = Depends(get_profile_service),
):
    """
    Obtener perfil completo del usuario autenticado.

    :param user_id: ID del usuario autenticado extraído del token JWT
    :param service: Servicio de perfiles
    :return: Perfil completo del usuario autenticado
    :rtype: UserResponse
    :raise HTTPException: Si el usuario no es encontrado
    """

    profile = await service.get_current_user_profile(user_id)

    return profile
