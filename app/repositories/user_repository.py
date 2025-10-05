from typing import Optional

from supabase import AsyncClient

from app.models.user import UserWithCompany


class UserRepository:
    """Repository para operaciones de base de datos relacionadas con usuarios"""

    def __init__(self, supabase_client: AsyncClient):
        self.supa = supabase_client

    async def get_user_with_company(self) -> Optional[UserWithCompany]:
        """Obtener usuario con información de su empresa"""
        try:
            res = (
                await self.supa.table("users")
                .select("""
                id,
                email,
                full_name,
                phone,
                role,
                company_id,
                created_at,
                company:company_id (
                    id,
                    legal_name,
                    tax_id
                )
            """)
                .single()
                .execute()
            )
            return UserWithCompany(**res.model_dump()["data"])
        except Exception:
            return None
