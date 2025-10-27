from datetime import UTC, datetime
from uuid import UUID

from pydantic import EmailStr
from sqlalchemy import TIMESTAMP
from sqlmodel import Column, Enum, Field, SQLModel, func

from app.core.enums import UserRole


class Profile(SQLModel, table=True):
    id: UUID = Field(primary_key=True, index=True)
    email: EmailStr = Field(max_length=255, index=True, nullable=False, unique=True)
    first_name: str | None = Field(max_length=100, default=None)
    last_name: str | None = Field(max_length=100, default=None)
    role: UserRole = Field(
        default=UserRole.applicant,
        sa_column=Column(
            Enum(UserRole, name="user_role", native_enum=True, create_type=False)
        ),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(
            TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
        ),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=func.now(),
            onupdate=func.now(),
        ),
    )

    __tablename__ = "profiles"  # type: ignore[assignment]
