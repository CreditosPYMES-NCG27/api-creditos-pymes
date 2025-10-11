from typing import Any

from supabase import AsyncClient


class ProfileRepository:
    """Repository para operaciones de base de datos relacionadas con usuarios"""

    def __init__(self, supabase_client: AsyncClient):
        self.supa = supabase_client

    async def get_user_by_id(self, user_id: str) -> Any:
        """
        Obtener un usuario específico por ID.

        Levanta excepción si el usuario no existe.

        :param user_id: ID del usuario
        :raises Exception: Si el usuario no se encuentra
        :return: Datos del usuario
        """
        try:
            res = (
                await self.supa.table("profiles")
                .select("*")
                .eq("id", user_id)
                .single()
                .execute()
            )
            if not res.data:
                raise Exception("Usuario no encontrado")
            return res.data
        except Exception as e:
            raise Exception(f"Error al obtener usuario: {str(e)}")
