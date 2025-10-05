from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from supabase import AsyncClient, acreate_client

from app.config import SUPABASE_ANON_KEY, SUPABASE_URL

bearer = HTTPBearer()


async def supabase_for_user(
    creds: HTTPAuthorizationCredentials = Depends(bearer),
) -> AsyncClient:
    token = creds.credentials
    supa: AsyncClient = await acreate_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    supa.postgrest.auth(token)  # RLS con JWT del usuario
    return supa
