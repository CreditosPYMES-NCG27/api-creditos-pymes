from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import TIMESTAMP
from sqlmodel import JSON, Column, Field, ForeignKeyConstraint, SQLModel, func


class Company(SQLModel, table=True):
    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        index=True,
        sa_column_kwargs={"server_default": func.gen_random_uuid()},
    )
    user_id: UUID = Field(unique=True, nullable=False, index=True)
    legal_name: str = Field(max_length=255, nullable=False)
    tax_id: str = Field(max_length=50, unique=True, nullable=False, index=True)
    contact_email: str = Field(max_length=255, nullable=False)
    contact_phone: str = Field(max_length=20, nullable=False)
    address: dict[str, Any] = Field(nullable=False, sa_type=JSON)
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

    __tablename__ = "companies"  # type: ignore[assignment]
    __table_args__ = (
        ForeignKeyConstraint(
            ["user_id"],
            ["profiles.id"],
            name="fk_companies_profile",
            ondelete="CASCADE",
        ),
    )
