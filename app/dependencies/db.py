# app/dependencies/db.py
from typing import AsyncGenerator

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession


async def get_session(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """Obtiene una sesión de database desde app.state."""
    session_maker = request.app.state.async_session
    async with session_maker() as session:
        try:
            yield session
        finally:
            if session.in_transaction():
                await session.rollback()
