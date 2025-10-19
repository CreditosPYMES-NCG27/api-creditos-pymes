from enum import StrEnum


class UserRole(StrEnum):
    """Roles válidos para usuarios del sistema."""

    applicant = "applicant"
    operator = "operator"
    admin = "admin"


class CreditApplicationStatus(StrEnum):
    """Estados válidos para la solicitud de crédito."""

    pending = "pending"
    in_review = "in_review"
    approved = "approved"
    rejected = "rejected"


class CreditApplicationPurpose(StrEnum):
    """Propósitos válidos para la solicitud de crédito (MVP)."""

    working_capital = "working_capital"
    equipment = "equipment"
    expansion = "expansion"
    inventory = "inventory"
    refinancing = "refinancing"
    other = "other"
