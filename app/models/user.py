from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class UserResponse(BaseModel):
    """Modelo básico de respuesta para usuario"""

    id: str
    email: str
    full_name: Optional[str]
    phone: Optional[str]
    role: str
    company_id: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserWithCompany(UserResponse):
    """Usuario con información de su empresa"""

    company: Optional[dict] = None
