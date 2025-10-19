from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.enums import UserRole
from app.models.profile import Profile


class ProfileRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def read(self, user_id: UUID) -> Profile | None:
        result = await self.session.execute(
            select(Profile).where(Profile.id == user_id)
        )
        return result.scalars().first()

    async def get_user_role(self, user_id: UUID) -> UserRole | None:
        result = await self.session.execute(
            select(Profile).where(Profile.id == user_id)
        )
        profile = result.scalars().first()
        return profile.role if profile else None
