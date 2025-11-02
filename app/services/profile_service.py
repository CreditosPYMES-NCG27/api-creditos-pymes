from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import UserRole
from app.core.errors import ForbiddenError, NotFoundError
from app.repositories.profiles_repository import ProfileRepository
from app.schemas.auth import Principal
from app.schemas.profile import ProfileResponse


class ProfileService:
    def __init__(self, session: AsyncSession):
        self.profile_repo = ProfileRepository(session)

    async def get_user_profile(self, user: Principal) -> ProfileResponse:
        """Devuelve el perfil del usuario autenticado.

        Args:
            user (Principal): Usuario autenticado.
        Returns:
            ProfileResponse: Perfil del usuario autenticado.
        """
        profile = await self.profile_repo.read(UUID(user.sub))
        if not profile:
            raise NotFoundError("Usuario no encontrado")
        return ProfileResponse.model_validate(profile.model_dump())

    async def get_profile_by_id(
        self, user_id: UUID, current: Principal
    ) -> ProfileResponse:
        """Obtiene el perfil por ID con reglas de autorización.

        - applicant: solo puede ver su propio perfil
        - operator/admin: pueden ver cualquier perfil

        Args:
            user_id (UUID): ID del usuario cuyo perfil se va a obtener.
            current (Principal): Usuario autenticado que realiza la solicitud.
        Returns:
            ProfileResponse: Perfil del usuario solicitado.
        """
        current_uuid = UUID(current.sub)
        if current_uuid != user_id:
            role = await self.profile_repo.get_user_role(current_uuid)
            if role not in (UserRole.admin, UserRole.operator):
                raise ForbiddenError("No tiene permisos para ver este perfil")

        profile = await self.profile_repo.read(user_id)
        if not profile:
            raise NotFoundError("Usuario no encontrado")
        return ProfileResponse.model_validate(profile.model_dump())
