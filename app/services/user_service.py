from typing import Optional

from supabase import AsyncClient

from app.models.user import UserWithCompany
from app.repositories.user_repository import UserRepository


class UserService:
    """Servicio para lógica de negocio relacionada con usuarios"""

    def __init__(self, supabase_client: AsyncClient):
        self.repository = UserRepository(supabase_client)

    async def get_current_user_profile(self) -> Optional[UserWithCompany]:
        """
        Obtener perfil completo del usuario actual.

        Args:
            user_id: ID del usuario autenticado

        Returns:
            Usuario con información de su empresa, o None si no existe
        """
        return await self.repository.get_user_with_company()
