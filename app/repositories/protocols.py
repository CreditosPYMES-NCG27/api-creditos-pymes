"""Protocols for repository interfaces following DIP (Dependency Inversion Principle)"""

from datetime import datetime
from typing import Any, Protocol, Sequence
from uuid import UUID

from app.core.enums import SignatureStatus, UserRole
from app.models.company import Company
from app.models.credit_application import CreditApplication
from app.models.document import Document


class ProfileRepositoryProtocol(Protocol):
    """Protocol for profile repository operations"""

    async def get_user_role(self, user_id: UUID) -> UserRole | None:
        """Get user role by user ID"""
        ...


class CompanyRepositoryProtocol(Protocol):
    """Protocol for company repository operations"""

    async def get_by_id(self, company_id: UUID) -> Company | None:
        """Get company by ID"""
        ...

    async def get_by_user_id(self, user_id: UUID) -> Company | None:
        """Get company by user ID"""
        ...

    async def update(self, company_id: UUID, data: dict[str, Any]) -> Company | None:
        """Update company data"""
        ...

    async def list(
        self,
        page: int = 1,
        limit: int = 20,
        sort: str | None = None,
        order: str = "desc",
    ) -> tuple[Sequence[Company], int]:
        """List companies with pagination"""
        ...


class CreditApplicationRepositoryProtocol(Protocol):
    """Protocol for credit application repository operations"""

    async def list_applications(
        self,
        page: int = 1,
        limit: int = 20,
        status: str | None = None,
        company_id: UUID | None = None,
        sort: str | None = None,
        order: str = "desc",
    ) -> tuple[Sequence[CreditApplication], int]:
        """List credit applications with pagination and filters"""
        ...

    async def create_application(
        self, application: CreditApplication
    ) -> CreditApplication:
        """Create a new credit application"""
        ...

    async def get_application_by_id(
        self, application_id: UUID
    ) -> CreditApplication | None:
        """Get credit application by ID"""
        ...

    async def check_company_has_pending_application(self, company_id: UUID) -> bool:
        """Check if company has pending applications"""
        ...

    async def update_application(
        self, application_id: UUID, data: dict[str, Any]
    ) -> CreditApplication | None:
        """Update credit application data"""
        ...


class DocumentRepositoryProtocol(Protocol):
    """Protocol for document repository operations"""

    async def get_by_id(self, document_id: UUID) -> Document | None:
        """Get document by ID"""
        ...

    async def get_by_storage_path(self, storage_path: str) -> Document | None:
        """Get document by storage path"""
        ...

    async def get_by_signature_request_id(
        self, signature_request_id: str
    ) -> Document | None:
        """Get document by DocuSign signature request ID (envelope ID)"""
        ...

    async def list_by_user(
        self, user_id: UUID, page: int = 1, limit: int = 20
    ) -> tuple[Sequence[Document], int]:
        """List documents by user ID with pagination"""
        ...

    async def list_by_application(
        self, application_id: UUID, page: int = 1, limit: int = 20
    ) -> tuple[Sequence[Document], int]:
        """List documents by credit application ID with pagination"""
        ...

    async def update_signature_status(
        self,
        document_id: UUID,
        signature_status: SignatureStatus,
        signature_request_id: str | None = None,
        signed_at: datetime | None = None,
        signed_file_path: str | None = None,
    ) -> Document | None:
        """Update document signature status and related fields"""
        ...
