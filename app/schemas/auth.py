from pydantic import BaseModel, EmailStr


class Principal(BaseModel):
    sub: str
    email: EmailStr | None = None
