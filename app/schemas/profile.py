from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserResponse(BaseModel):
    """Modelo básico de respuesta para usuario"""

    id: str
    email: str
    full_name: str | None
    phone: str | None
    role: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
