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
