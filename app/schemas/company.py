from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class CompanyAddress(BaseModel):
    street: str = Field(..., description="Street address")
    city: str = Field(..., description="City name")
    state: str = Field(..., description="State or province")
    zip_code: str = Field(..., description="ZIP or postal code")
    country: str = Field(..., description="Country name")


class CompanyResponse(BaseModel):
    """Esquema de empresa"""

    id: Annotated[UUID, Field(description="ID único de la empresa")]
    user_id: Annotated[
        UUID, Field(description="ID del usuario propietario de la empresa")
    ]
    legal_name: Annotated[str, Field(description="Nombre legal de la empresa")]
    tax_id: Annotated[
        str, Field(description="Número de identificación fiscal de la empresa")
    ]
    contact_email: Annotated[
        EmailStr, Field(description="Correo electrónico de contacto")
    ]
    contact_phone: Annotated[str, Field(description="Teléfono de contacto")]
    address: Annotated[CompanyAddress, Field(description="Dirección de la empresa")]
    created_at: Annotated[
        datetime, Field(description="Fecha de creación de la empresa")
    ]
    updated_at: Annotated[
        datetime, Field(description="Fecha de actualización de la empresa")
    ]


class CompanyUpdate(BaseModel):
    """Modelo para actualizar una empresa (campos opcionales)"""

    contact_email: Annotated[str | None, Field(min_length=1, max_length=255)] = None
    contact_phone: Annotated[str | None, Field(min_length=1, max_length=20)] = None
    address: Annotated[CompanyAddress | None, Field()] = None
