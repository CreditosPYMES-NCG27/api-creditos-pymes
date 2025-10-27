from uuid import UUID

from fastapi import APIRouter

from app.dependencies.auth import CurrentUserDep
from app.dependencies.services import ProfileServiceDep
from app.schemas.profile import ProfileResponse

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.get("/me", response_model=ProfileResponse)
async def read_my_profile(
    service: ProfileServiceDep,
    user: CurrentUserDep,
):
    """Devuelve el perfil del usuario autenticado."""
    profile = await service.get_user_profile(user)
    return profile


@router.get("/{user_id}", response_model=ProfileResponse)
async def read_profile_by_id(
    user_id: UUID,
    service: ProfileServiceDep,
    user: CurrentUserDep,
):
    """Obtiene el perfil de un usuario por ID.

    - applicant: solo puede ver su propio perfil
    - operator/admin: pueden ver cualquier perfil
    """
    return await service.get_profile_by_id(user_id, user)
