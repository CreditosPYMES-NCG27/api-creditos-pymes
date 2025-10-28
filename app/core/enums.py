from enum import StrEnum


class UserRole(StrEnum):
    """Roles válidos para usuarios del sistema."""

    applicant = "applicant"
    operator = "operator"
    admin = "admin"


class CreditApplicationStatus(StrEnum):
    """Estados válidos para la solicitud de crédito."""

    draft = "draft"
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


class DocumentType(StrEnum):
    """Tipos de documento válidos."""

    tax_return = "tax_return"
    financial_statement = "financial_statement"
    id_document = "id_document"
    business_license = "business_license"
    bank_statement = "bank_statement"
    other = "other"


class DocumentStatus(StrEnum):
    """Estados válidos para documentos."""

    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class SignatureStatus(StrEnum):
    """Estados de firma de documento."""

    unsigned = "unsigned"
    pending = "pending"
    signed = "signed"
    declined = "declined"
