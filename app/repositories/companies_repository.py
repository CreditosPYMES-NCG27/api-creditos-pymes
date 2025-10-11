from typing import Any, Dict, List
from uuid import UUID

from supabase import AsyncClient


class CompanyRepository:
    def __init__(self, supabase_client: AsyncClient):
        self.supabase = supabase_client

    async def list_companies(
        self,
        page: int = 1,
        limit: int = 20,
        status: str | None = None,
        search: str | None = None,
    ) -> List[Dict[str, Any]]:
        query = self.supabase.table("companies").select("*")

        if status:
            query = query.eq("status", status)
        if search:
            query = query.or_(f"legal_name.ilike.%{search}%,tax_id.ilike.%{search}%")

        offset = (page - 1) * limit
        query = query.range(offset, offset + limit - 1)

        res: Any = await query.execute()
        return res.data

    async def create_company(self, company_data: Dict[str, Any]) -> Dict[str, Any]:
        res: Any = await self.supabase.table("companies").insert(company_data).execute()
        if not res.data:
            raise Exception("Error al crear la empresa")
        return res.data[0]

    async def get_company_by_id(self, company_id: UUID) -> Dict[str, Any]:
        res: Any = (
            await self.supabase.table("companies")
            .select("*")
            .eq("id", str(company_id))
            .execute()
        )
        if not res.data:
            raise Exception("Empresa no encontrada")
        return res.data[0]

    async def get_company_by_user_id(self, user_id: str) -> Dict[str, Any]:
        res: Any = (
            await self.supabase.table("companies")
            .select("*")
            .eq("user_id", user_id)
            .execute()
        )
        if not res.data:
            raise Exception("Empresa no encontrada")
        return res.data[0]

    async def update_company(
        self, company_id: UUID, update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        res: Any = (
            await self.supabase.table("companies")
            .update(update_data)
            .eq("id", str(company_id))
            .execute()
        )
        if not res.data:
            raise Exception("Error al actualizar la empresa")
        return res.data[0]

    async def check_company_exists_by_tax_id(
        self, tax_id: str, exclude_id: UUID | None = None
    ) -> bool:
        query = self.supabase.table("companies").select("id").eq("tax_id", tax_id)
        if exclude_id:
            query = query.neq("id", str(exclude_id))
        res: Any = await query.execute()
        return len(res.data) > 0

    async def check_user_has_company(self, user_id: str) -> bool:
        res: Any = (
            await self.supabase.table("companies")
            .select("id")
            .eq("user_id", user_id)
            .execute()
        )
        return len(res.data) > 0
