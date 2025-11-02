from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import CreditApplicationPurpose, CreditApplicationStatus, UserRole
from app.core.errors import ForbiddenError, NotFoundError, ValidationDomainError
from app.models.credit_application import CreditApplication
from app.repositories.companies_repository import CompanyRepository
from app.repositories.credit_applications_repository import CreditApplicationRepository
from app.repositories.protocols import (
    CompanyRepositoryProtocol,
    CreditApplicationRepositoryProtocol,
    ProfileRepositoryProtocol,
)
from app.schemas.auth import Principal
from app.schemas.credit_application import (
    CreditApplicationCreate,
    CreditApplicationResponse,
    CreditApplicationUpdate,
)
from app.schemas.pagination import Paginated
from app.services.base_service import BaseService


class CreditApplicationService(BaseService):
    """Servicio para lógica de negocio de aplicaciones de crédito"""

    def __init__(
        self,
        session: AsyncSession,
        app_repo: CreditApplicationRepositoryProtocol | None = None,
        company_repo: CompanyRepositoryProtocol | None = None,
        profile_repo: ProfileRepositoryProtocol | None = None,
    ):
        super().__init__(session, profile_repo)
        self.app_repo = app_repo or CreditApplicationRepository(session)
        self.company_repo = company_repo or CompanyRepository(session)

    async def list_applications(
        self,
        user: Principal,
        page: int = 1,
        limit: int = 20,
        status: CreditApplicationStatus | None = None,
        company_id: UUID | None = None,
        sort: str | None = None,
        order: str = "desc",
    ) -> Paginated[CreditApplicationResponse]:
        role = await self.assert_role(user.sub)
        exclude_status_list: list[CreditApplicationStatus] | None = None

        if role == UserRole.applicant:
            # Applicants solo ven sus propias aplicaciones
            user_company = await self.company_repo.get_by_user_id(UUID(user.sub))
            if not user_company:
                meta = BaseService.create_pagination_meta(
                    total=0,
                    page=page,
                    per_page=limit,
                )
                return Paginated[CreditApplicationResponse](
                    items=[],
                    meta=meta,
                )
            company_id = user_company.id
        else:
            # Operators/admins NO ven solicitudes en draft
            # Si no se especificó status, excluir draft implícitamente
            # Si se especificó draft explícitamente, lanzar error
            if status == CreditApplicationStatus.draft:
                raise ForbiddenError(
                    "Los operadores y administradores no pueden ver solicitudes en borrador"
                )
            # Excluir drafts de la query SQL
            exclude_status_list = [CreditApplicationStatus.draft]

        items, total = await self.app_repo.list_applications(
            page=page,
            limit=limit,
            status=status,
            company_id=company_id,
            sort=sort,
            order=order,
            exclude_status=exclude_status_list,
        )

        meta = BaseService.create_pagination_meta(
            total=total,
            page=page,
            per_page=limit,
        )
        return Paginated[CreditApplicationResponse](
            items=[
                CreditApplicationResponse.model_validate(application.model_dump())
                for application in items
            ],
            meta=meta,
        )

    async def get_application_by_id(
        self, application_id: UUID, user: Principal
    ) -> CreditApplicationResponse:
        role = await self.assert_role(user.sub)
        application = await self.app_repo.get_application_by_id(application_id)
        if not application:
            raise NotFoundError("Solicitud no encontrada")
        if role == UserRole.applicant:
            # Verificar que la app pertenece a la company del user
            user_company = await self.company_repo.get_by_user_id(UUID(user.sub))
            if not user_company or application.company_id != user_company.id:
                raise ForbiddenError("No autorizado para ver esta solicitud")
        # Operators/admins pueden ver todas
        return CreditApplicationResponse.model_validate(application.model_dump())

    async def create_application(
        self, application: CreditApplicationCreate, user: Principal
    ) -> CreditApplicationResponse:
        user_role = await self.assert_role(user.sub)

        if user_role is not UserRole.applicant:
            print(user_role)
            raise ForbiddenError(
                "Solo los solicitantes pueden crear solicitudes de crédito"
            )

        company = await self.company_repo.get_by_user_id(UUID(user.sub))

        if not company:
            raise ValidationDomainError(
                "Debes registrar una empresa antes de solicitar crédito"
            )

        if application.status not in {
            CreditApplicationStatus.pending,
            CreditApplicationStatus.draft,
        }:
            raise ValidationDomainError(
                f"Estado {application.status} no permitido para solicitantes"
            )

        if (
            application.purpose is CreditApplicationPurpose.other
            and not application.purpose_other
        ):
            raise ValidationDomainError(
                "El campo 'purpose_other' es requerido cuando 'purpose' se establece en 'other'"
            )

        data = application.model_dump()
        data["company_id"] = company.id
        app_model = CreditApplication(**data)
        created = await self.app_repo.create_application(app_model)
        return CreditApplicationResponse.model_validate(created.model_dump())

    async def update_application(
        self,
        user: Principal,
        application_id: UUID,
        application: CreditApplicationUpdate,
    ) -> CreditApplicationResponse:
        """Actualiza parcialmente una aplicación de crédito según permisos:
        - Applicants: pueden editar sus propias solicitudes en estado 'draft'. No pueden editar solicitudes en estado 'pending' o superior.
        - Operators/Admins: pueden editar cualquier solicitud que no esté en estado 'draft'.
        """
        user_role = await self.assert_role(user.sub)
        user_company = await self.company_repo.get_by_user_id(UUID(user.sub))
        existing_app = await self.app_repo.get_application_by_id(application_id)
        update_data = {
            k: v for k, v in application.model_dump().items() if v is not None
        }

        if not user_company:
            raise ForbiddenError("Usuario no tiene ninguna empresa registrada")

        if not existing_app:
            raise NotFoundError("Solicitud no encontrada")

        if existing_app.company_id != user_company.id:
            raise ForbiddenError("Solicitud no pertenece a este usuario")

        if user_role == UserRole.applicant:
            if existing_app.status == CreditApplicationStatus.pending:
                raise ForbiddenError("No puede editar una solicitud ya enviada")

            if application.status not in {
                CreditApplicationStatus.pending,
                CreditApplicationStatus.draft,
            }:
                raise ForbiddenError(
                    f"Estado {application.status} no permitido para solicitantes"
                )
            # Debemos ignorar risk_score y approved_amount si el user_role es applicant
            update_data.pop("risk_score", None)
            update_data.pop("approved_amount", None)
        elif user_role == UserRole.operator or user_role == UserRole.admin:
            if existing_app.status == CreditApplicationStatus.draft:
                raise ForbiddenError(
                    "Los operadores/administradores no pueden modificar solicitudes en borrador"
                )

            if application.status == CreditApplicationStatus.draft:
                raise ForbiddenError(
                    "Estado no permitido para operadores/administradores"
                )

        if (
            application.purpose is CreditApplicationPurpose.other
            and not application.purpose_other
        ):
            raise ValidationDomainError(
                "El campo 'purpose_other' es requerido cuando 'purpose' se establece en 'other'"
            )

        if not update_data:
            raise ValidationDomainError("No se proporcionaron campos para actualizar")

        updated = await self.app_repo.update_application(application_id, update_data)

        if not updated:
            raise ValidationDomainError("Error al actualizar la aplicación")

        return CreditApplicationResponse.model_validate(updated.model_dump())

    async def delete_application(self, user: Principal, application_id: UUID) -> None:
        """Elimina una aplicación de crédito según permisos:

        - Applicants: solo pueden eliminar sus propias aplicaciones en estado 'draft' o 'pending'.
        - Operators/Admins: pueden eliminar (permiso elevado).
        """
        role = await self.assert_role(user.sub)

        existing_app = await self.app_repo.get_application_by_id(application_id)
        if not existing_app:
            raise NotFoundError("Solicitud no encontrada")

        if role == UserRole.applicant:
            user_company = await self.company_repo.get_by_user_id(UUID(user.sub))
            if not user_company or existing_app.company_id != user_company.id:
                raise ForbiddenError("No autorizado para eliminar esta solicitud")
            # Applicants pueden borrar solicitudes en estado 'draft' solamente
            if existing_app.status != CreditApplicationStatus.draft:
                raise ForbiddenError("Solo se pueden eliminar solicitudes en borrador")

        # Operators y admins pueden eliminar (operación permitida)

        deleted = await self.app_repo.delete_application(application_id)
        if not deleted:
            raise ValidationDomainError("Error al eliminar la aplicación")
