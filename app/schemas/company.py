from datetime import date, datetime
from typing import Any, Dict
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CompanyBase(BaseModel):
    """Modelo base para empresa con campos comunes"""

    legal_name: str = Field(..., min_length=1, max_length=255)
    tax_id: str = Field(..., min_length=1, max_length=50)
    contact_name: str = Field(..., min_length=1, max_length=255)
    contact_email: str = Field(..., min_length=1, max_length=255)
    contact_phone: str = Field(..., min_length=1, max_length=20)
    address: Dict[str, Any] = Field(
        ...
    )  # JSONB: {street, city, state, country, postal_code}
    industry: str | None = Field(None, max_length=100)
    foundation_date: date | None = None
    status: str = Field(default="active", pattern="^(active|inactive|blacklisted)$")


class CompanyCreate(CompanyBase):
    """Modelo para crear una nueva empresa"""

    pass


class CompanyUpdate(BaseModel):
    """Modelo para actualizar una empresa (campos opcionales)"""

    legal_name: str | None = Field(None, min_length=1, max_length=255)
    tax_id: str | None = Field(None, min_length=1, max_length=50)
    contact_name: str | None = Field(None, min_length=1, max_length=255)
    contact_email: str | None = Field(None, min_length=1, max_length=255)
    contact_phone: str | None = Field(None, min_length=1, max_length=20)
    address: Dict[str, Any] | None = None
    industry: str | None = Field(None, max_length=100)
    foundation_date: date | None = None
    status: str | None = Field(None, pattern="^(active|inactive|blacklisted)$")


class CompanyResponse(CompanyBase):
    """Modelo de respuesta para empresa"""

    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CompanyWithUser(CompanyResponse):
    """Empresa con información de su usuario propietario"""

    user: dict | None = None
