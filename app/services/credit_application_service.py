from datetime import datetime, timezone
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
        # Operators/admins ven todas, o filtradas por company_id si especificado
        items, total = await self.app_repo.list_applications(
            page=page,
            limit=limit,
            status=status,
            company_id=company_id,
            sort=sort,
            order=order,
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

    async def create_application(
        self, application: CreditApplicationCreate, user: Principal
    ) -> CreditApplicationResponse:
        company = await self.company_repo.get_by_user_id(UUID(user.sub))
        if not company:
            raise ValidationDomainError(
                "Debes registrar una empresa antes de solicitar crédito"
            )

        if await self.app_repo.check_company_has_pending_application(company.id):
            raise ValidationDomainError("Ya tienes una solicitud pendiente")

        # Validar que si purpose es 'other', purpose_other sea requerido
        if application.purpose == CreditApplicationPurpose.other:
            if not application.purpose_other or not application.purpose_other.strip():
                raise ValidationDomainError(
                    "purpose_other es requerido cuando purpose es 'other'"
                )

        data = application.model_dump()
        data["company_id"] = company.id

        app_model = CreditApplication(**data)
        created = await self.app_repo.create_application(app_model)
        return CreditApplicationResponse.model_validate(created.model_dump())

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

    async def update_application(
        self,
        user: Principal,
        application_id: UUID,
        application: CreditApplicationUpdate,
    ) -> CreditApplicationResponse:
        await self.assert_role(user.sub, UserRole.operator, UserRole.admin)
        update_data = {
            k: v for k, v in application.model_dump().items() if v is not None
        }
        if not update_data:
            raise ValidationDomainError("No se proporcionaron campos para actualizar")

        # Obtener la aplicación existente para validaciones de dominio
        existing_app = await self.app_repo.get_application_by_id(application_id)
        if not existing_app:
            raise NotFoundError("Solicitud no encontrada")

        # Validaciones de dominio
        await self._validate_application_update(existing_app, update_data)

        updated = await self.app_repo.update_application(application_id, update_data)
        if not updated:
            raise ValidationDomainError("Error al actualizar la aplicación")
        return CreditApplicationResponse.model_validate(updated.model_dump())

    async def _validate_application_update(
        self,
        existing_app: CreditApplication,
        update_data: dict,
    ) -> None:
        """Valida las reglas de negocio para actualizar una aplicación de crédito.

        Args:
            existing_app: La aplicación existente antes de la actualización
            update_data: Los datos que se van a actualizar

        Raises:
            ValidationDomainError: Si se violan las reglas de negocio
        """
        new_status = update_data.get("status", existing_app.status)

        # Validar transiciones de estado: pending → in_review → approved/rejected
        if "status" in update_data:
            self._validate_status_transition(existing_app.status, new_status)

        # Validaciones específicas por estado
        if new_status == CreditApplicationStatus.approved:
            self._validate_approved_status(update_data, existing_app)
        elif new_status == CreditApplicationStatus.rejected:
            self._validate_rejected_status(update_data)

        # Validar cambio de purpose a "other"
        if "purpose" in update_data:
            new_purpose = update_data["purpose"]
            if new_purpose == CreditApplicationPurpose.other:
                if (
                    "purpose_other" not in update_data
                    or not update_data["purpose_other"]
                ):
                    raise ValidationDomainError(
                        "purpose_other es requerido cuando purpose es 'other'"
                    )

        # Si approved_amount está presente, debe ser válido
        if "approved_amount" in update_data:
            approved_amount = update_data["approved_amount"]
            if approved_amount <= 0:
                raise ValidationDomainError("approved_amount debe ser mayor que 0")
            if approved_amount > existing_app.requested_amount:
                raise ValidationDomainError(
                    f"approved_amount ({approved_amount}) no puede ser mayor que "
                    f"requested_amount ({existing_app.requested_amount})"
                )

        # Si interest_rate está presente, debe ser válido
        # (validación ge=0 ya cubierta por el schema)

    def _validate_status_transition(
        self,
        current_status: CreditApplicationStatus,
        new_status: CreditApplicationStatus,
    ) -> None:
        """Valida que las transiciones de estado sean válidas.

        Args:
            current_status: Estado actual
            new_status: Nuevo estado

        Raises:
            ValidationDomainError: Si la transición no es válida
        """
        valid_transitions = {
            CreditApplicationStatus.pending: [
                CreditApplicationStatus.in_review,
                CreditApplicationStatus.approved,
                CreditApplicationStatus.rejected,
            ],
            CreditApplicationStatus.in_review: [
                CreditApplicationStatus.approved,
                CreditApplicationStatus.rejected,
            ],
            CreditApplicationStatus.approved: [],  # No se puede cambiar una vez aprobado
            CreditApplicationStatus.rejected: [],  # No se puede cambiar una vez rechazado
        }

        if new_status not in valid_transitions[current_status]:
            raise ValidationDomainError(
                f"Transición de estado no válida: {current_status} → {new_status}. "
                f"Transiciones permitidas desde {current_status}: "
                f"{[valid_status for valid_status in valid_transitions[current_status]]}"
            )

    def _validate_approved_status(
        self, update_data: dict, existing_app: CreditApplication
    ) -> None:
        """Valida reglas específicas cuando el estado cambia a approved.

        Args:
            update_data: Datos de actualización
            existing_app: Aplicación existente

        Raises:
            ValidationDomainError: Si se violan las reglas
        """
        # approved_amount es obligatorio
        if (
            "approved_amount" not in update_data
            and existing_app.approved_amount is None
        ):
            raise ValidationDomainError(
                "approved_amount es requerido cuando el status es 'approved'"
            )

        # interest_rate es obligatorio
        if "interest_rate" not in update_data and existing_app.interest_rate is None:
            raise ValidationDomainError(
                "interest_rate es requerido cuando el status es 'approved'"
            )

        # Validar approved_amount <= requested_amount (si está presente)
        if "approved_amount" in update_data:
            approved_amount = update_data["approved_amount"]
            if approved_amount > existing_app.requested_amount:
                raise ValidationDomainError(
                    f"approved_amount ({approved_amount}) no puede ser mayor que "
                    f"requested_amount ({existing_app.requested_amount})"
                )

        # Fijar reviewed_at si no viene
        if "reviewed_at" not in update_data:
            update_data["reviewed_at"] = datetime.now(timezone.utc)

    def _validate_rejected_status(self, update_data: dict) -> None:
        """Valida reglas específicas cuando el estado cambia a rejected.

        Args:
            update_data: Datos de actualización

        Raises:
            ValidationDomainError: Si se violan las reglas
        """
        # review_notes es obligatorio para trazabilidad
        if "review_notes" not in update_data or not update_data["review_notes"]:
            raise ValidationDomainError(
                "review_notes es requerido cuando el status es 'rejected'"
            )
