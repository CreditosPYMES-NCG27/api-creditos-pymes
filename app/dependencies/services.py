from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.dependencies.db import get_session
from app.services.company_service import CompanyService
from app.services.credit_application_service import CreditApplicationService
from app.services.document_service import DocumentService
from app.services.profile_service import ProfileService


def get_profile_service(session: AsyncSession = Depends(get_session)) -> ProfileService:
    return ProfileService(session)


def get_company_service(session: AsyncSession = Depends(get_session)) -> CompanyService:
    return CompanyService(session)


def get_credit_application_service(
    session: AsyncSession = Depends(get_session),
) -> CreditApplicationService:
    return CreditApplicationService(session)


def get_document_service(
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> DocumentService:
    return DocumentService(session, settings)


ProfileServiceDep = Annotated[ProfileService, Depends(get_profile_service)]
CompanyServiceDep = Annotated[CompanyService, Depends(get_company_service)]
CreditApplicationServiceDep = Annotated[
    CreditApplicationService, Depends(get_credit_application_service)
]
DocumentServiceDep = Annotated[DocumentService, Depends(get_document_service)]
