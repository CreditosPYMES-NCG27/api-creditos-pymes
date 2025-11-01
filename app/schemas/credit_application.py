from datetime import datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.enums import CreditApplicationPurpose, CreditApplicationStatus


class CreditApplicationCreate(BaseModel):
    """Modelo para crear una nueva solicitud de crédito"""

    requested_amount: Annotated[
        Decimal, Field(..., gt=0, description="Monto solicitado")
    ]
    term_months: Annotated[int, Field(..., ge=1, le=360, description="Plazo en meses")]
    interest_rate: Annotated[Decimal, Field(10, gt=0, description="Tasa de interés")]
    status: Annotated[
        CreditApplicationStatus,
        Field(
            CreditApplicationStatus.pending,
            description="Estado de la solicitud (por defecto pending, puede ser draft)",
        ),
    ]
    purpose: Annotated[
        CreditApplicationPurpose, Field(..., description="Propósito del crédito")
    ]
    purpose_other: Annotated[str | None, Field(None, description="Otro propósito")]


class CreditApplicationUpdate(BaseModel):
    """Modelo para actualizar una solicitud (solo operadores)"""

    requested_amount: Annotated[
        Decimal | None, Field(None, gt=0, description="Monto solicitado")
    ]
    term_months: Annotated[
        int | None, Field(None, ge=1, le=360, description="Plazo en meses")
    ]
    interest_rate: Annotated[
        Decimal | None, Field(None, gt=0, description="Tasa de interés")
    ]
    status: Annotated[
        CreditApplicationStatus | None, Field(None, description="Nuevo estado")
    ]
    purpose: Annotated[
        CreditApplicationPurpose | None,
        Field(None, description="Propósito del crédito"),
    ]
    purpose_other: Annotated[str | None, Field(None, description="Otro propósito")]
    risk_score: Annotated[
        Decimal | None,
        Field(None, ge=0, le=100, description="Puntaje de riesgo (solo operadores)"),
    ]
    approved_amount: Annotated[
        Decimal | None,
        Field(None, gt=0, description="Monto aprobado (solo operadores)"),
    ]


class CreditApplicationResponse(BaseModel):
    """Modelo de respuesta para solicitud de crédito"""

    id: Annotated[UUID, Field(description="ID único de la solicitud")]
    company_id: Annotated[UUID, Field(description="ID de la empresa")]
    requested_amount: Annotated[
        Decimal, Field(..., gt=0, description="Monto solicitado")
    ]
    purpose: Annotated[
        CreditApplicationPurpose, Field(..., description="Propósito del crédito")
    ]
    purpose_other: Annotated[str | None, Field(description="Otro propósito")]
    term_months: Annotated[int, Field(..., ge=1, le=360, description="Plazo en meses")]
    status: Annotated[
        CreditApplicationStatus,
        Field(
            default=CreditApplicationStatus.pending,
            description="Estado de la solicitud",
        ),
    ]
    risk_score: Annotated[Decimal | None, Field(description="Puntaje de riesgo")]
    approved_amount: Annotated[Decimal | None, Field(description="Monto aprobado")]
    interest_rate: Annotated[Decimal | None, Field(description="Tasa de interés")]
    created_at: Annotated[datetime, Field(description="Fecha de creación")]
    updated_at: Annotated[datetime, Field(description="Fecha de actualización")]


class CreditPurposeResponse(BaseModel):
    """Modelo de respuesta para propósitos de crédito"""

    value: Annotated[int, Field(description="Valor numérico para orden")]
    slug: Annotated[str, Field(description="Slug interno")]
    label: Annotated[str, Field(description="Texto para display")]
