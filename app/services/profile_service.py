from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.repositories.profiles_repository import ProfileRepository
from app.schemas.auth import Principal
from app.schemas.profile import ProfileResponse


class ProfileService:
    def __init__(self, session: AsyncSession):
        self.profile_repo = ProfileRepository(session)

    async def get_user_profile(self, user: Principal) -> ProfileResponse:
        profile = await self.profile_repo.read(UUID(user.sub))
        if not profile:
            raise NotFoundError("Usuario no encontrado")
        return ProfileResponse.model_validate(profile.model_dump())
