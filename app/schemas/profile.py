from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.core.enums import UserRole


class ProfileResponse(BaseModel):
    """Modelo de perfil de usuario"""

    id: Annotated[UUID, Field(description="ID único del perfil")]
    email: Annotated[EmailStr, Field(description="Correo electrónico del usuario")]
    first_name: Annotated[str | None, Field(description="Nombre(s) del usuario")]
    last_name: Annotated[str | None, Field(description="Apellido(s) del usuario")]
    role: Annotated[UserRole, Field(description="Rol del usuario")]
    created_at: Annotated[datetime, Field(description="Fecha de creación del perfil")]
    updated_at: Annotated[
        datetime, Field(description="Fecha de actualización del perfil")
    ]
