from typing import Any, Dict, List
from uuid import UUID

from supabase import AsyncClient


class CreditApplicationRepository:
    def __init__(self, supabase_client: AsyncClient):
        self.supabase = supabase_client

    async def list_applications(
        self,
        page: int = 1,
        limit: int = 20,
        status: str | None = None,
        company_id: str | None = None,
    ) -> List[Dict[str, Any]]:
        query = self.supabase.table("credit_applications").select("*")

        if status:
            query = query.eq("status", status)
        if company_id:
            query = query.eq("company_id", company_id)

        offset = (page - 1) * limit
        query = query.range(offset, offset + limit - 1)

        res: Any = await query.execute()
        return res.data

    async def create_application(
        self, application_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        res: Any = (
            await self.supabase.table("credit_applications")
            .insert(application_data)
            .execute()
        )
        if not res.data:
            raise Exception("Error al crear la solicitud")
        return res.data[0]

    async def get_application_by_id(self, application_id: UUID) -> Dict[str, Any]:
        res: Any = (
            await self.supabase.table("credit_applications")
            .select("*")
            .eq("id", str(application_id))
            .execute()
        )
        if not res.data:
            raise Exception(f"Solicitud con ID {application_id} no encontrada")
        return res.data[0]

    async def update_application(
        self, application_id: UUID, update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        res: Any = (
            await self.supabase.table("credit_applications")
            .update(update_data)
            .eq("id", str(application_id))
            .execute()
        )
        if not res.data:
            raise Exception("Error al actualizar la solicitud")
        return res.data[0]

    async def check_company_has_pending_application(self, company_id: UUID | str) -> bool:
        res: Any = (
            await self.supabase.table("credit_applications")
            .select("id")
            .eq("company_id", str(company_id))
            .eq("status", "pending")
            .execute()
        )
        return len(res.data) > 0
