"""Protocols for repository interfaces following DIP (Dependency Inversion Principle)"""

from typing import Any, Protocol, Sequence
from uuid import UUID

from app.core.enums import UserRole
from app.models.company import Company
from app.models.credit_application import CreditApplication


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
