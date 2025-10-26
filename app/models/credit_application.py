from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import TIMESTAMP
from sqlmodel import (
    CheckConstraint,
    Column,
    Enum,
    Field,
    ForeignKeyConstraint,
    SQLModel,
    func,
)

from app.core.enums import CreditApplicationPurpose, CreditApplicationStatus


class CreditApplication(SQLModel, table=True):
    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        index=True,
        sa_column_kwargs={"server_default": func.gen_random_uuid()},
    )
    company_id: UUID = Field(nullable=False, index=True)
    requested_amount: Decimal = Field(
        max_digits=15,
        decimal_places=2,
        nullable=False,
        gt=0,
    )
    purpose: CreditApplicationPurpose = Field(
        sa_column=Column(
            Enum(
                CreditApplicationPurpose,
                name="credit_application_purpose",
                native_enum=True,
                create_type=False,
            )
        ),
    )
    purpose_other: str | None = Field(default=None)
    term_months: int = Field(nullable=False, ge=1, le=360)
    status: CreditApplicationStatus = Field(
        default=CreditApplicationStatus.pending,
        sa_column=Column(
            Enum(
                CreditApplicationStatus,
                name="credit_application_status",
                native_enum=True,
                create_type=False,
            )
        ),
    )
    risk_score: Decimal | None = Field(
        max_digits=5,
        decimal_places=2,
        ge=0,
        le=100,
    )
    approved_amount: Decimal | None = Field(
        max_digits=15,
        decimal_places=2,
        ge=0,
    )
    interest_rate: Decimal | None = Field(
        default=None, max_digits=5, decimal_places=2, ge=0
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

    __tablename__ = "credit_applications"  # type: ignore[assignment]
    __table_args__ = (
        CheckConstraint(
            "(purpose != 'other') OR (purpose_other IS NOT NULL)",
            name="check_purpose_other",
        ),
        ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            name="fk_credit_applications_company",
            ondelete="CASCADE",
        ),
    )
