from supabase import AsyncClient

from app.repositories.profiles_repository import ProfileRepository
from app.schemas.profile import UserResponse


class ProfileService:
    """Servicio para lógica de negocio relacionada con usuarios"""

    def __init__(self, supabase_client: AsyncClient):
        self.repository = ProfileRepository(supabase_client)

    async def get_current_user_profile(self, user_id: str) -> UserResponse:
        """
        Obtener perfil del usuario actual.

        :param user_id: ID del usuario autenticado
        :return: Datos del perfil del usuario
        :raises Exception: Si el usuario no existe
        """
        user_data = await self.repository.get_user_by_id(user_id)
        return UserResponse(**user_data)
