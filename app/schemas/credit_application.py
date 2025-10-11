from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CreditPurpose(StrEnum):
    """Propósitos válidos para la solicitud de crédito (MVP)."""

    working_capital = "working_capital"
    equipment = "equipment"
    expansion = "expansion"
    inventory = "inventory"
    refinancing = "refinancing"
    other = "other"


PURPOSE_LABELS: dict[CreditPurpose, str] = {
    CreditPurpose.working_capital: "Capital de trabajo",
    CreditPurpose.equipment: "Equipamiento",
    CreditPurpose.expansion: "Expansión",
    CreditPurpose.inventory: "Inventario",
    CreditPurpose.refinancing: "Refinanciamiento",
    CreditPurpose.other: "Otro",
}


class CreditApplicationBase(BaseModel):
    """Modelo base para solicitud de crédito"""

    requested_amount: float = Field(..., gt=0)
    term_months: int = Field(..., ge=1, le=360)
    purpose: CreditPurpose = Field(..., description="Propósito del crédito")
    status: str = Field(
        default="pending", pattern="^(pending|in_review|approved|rejected)$"
    )


class CreditApplicationCreate(CreditApplicationBase):
    """Modelo para crear una nueva solicitud de crédito"""

    pass


class CreditApplicationUpdate(BaseModel):
    """Modelo para actualizar una solicitud (solo operadores)"""

    status: str | None = Field(None, pattern="^(pending|in_review|approved|rejected)$")
    risk_score: float | None = Field(None, ge=0, le=100)
    operator_id: UUID | None = None
    reviewed_at: datetime | None = None


class CreditApplicationResponse(CreditApplicationBase):
    """Modelo de respuesta para solicitud de crédito"""

    id: UUID
    company_id: UUID
    risk_score: float | None
    operator_id: UUID | None
    reviewed_at: datetime | None
    review_notes: str | None
    approved_amount: float | None
    interest_rate: float | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
