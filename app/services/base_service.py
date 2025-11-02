from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import UserRole
from app.core.errors import ForbiddenError
from app.repositories.profiles_repository import ProfileRepository
from app.repositories.protocols import ProfileRepositoryProtocol
from app.schemas.pagination import PaginationMeta


class BaseService:
    """Servicio base con lógica común de autorización"""

    def __init__(
        self,
        session: AsyncSession,
        profile_repo: ProfileRepositoryProtocol | None = None,
    ):
        self.session = session
        self.profile_repo = profile_repo or ProfileRepository(session)

    async def assert_role(self, user_sub: str, *allowed: UserRole) -> UserRole:
        """Verifica que el usuario tenga uno de los roles permitidos.

        Args:
            user_sub: ID del usuario como string
            *allowed: Roles permitidos (UserRole enum values)

        Returns:
            UserRole: El rol del usuario si está autorizado

        Raises:
            ForbiddenError: Si el usuario no tiene rol o no está autorizado
        """
        user_role = await self.profile_repo.get_user_role(UUID(user_sub))
        if user_role is None:
            raise ForbiddenError("Perfil sin rol")

        if allowed and user_role not in allowed:
            raise ForbiddenError("Rol no autorizado")

        return user_role

    async def has_role(self, user_sub: str, role: UserRole) -> bool:
        """Verifica si el usuario tiene un rol específico.

        Args:
            user_sub: ID del usuario como string
            role: Rol a verificar

        Returns:
            bool: True si el usuario tiene el rol
        """
        try:
            user_role = await self.assert_role(user_sub)
            return user_role == role
        except ForbiddenError:
            return False

    async def is_admin(self, user_sub: str) -> bool:
        """Verifica si el usuario es administrador."""
        return await self.has_role(user_sub, UserRole.admin)

    async def is_operator(self, user_sub: str) -> bool:
        """Verifica si el usuario es operador."""
        return await self.has_role(user_sub, UserRole.operator)

    async def is_applicant(self, user_sub: str) -> bool:
        """Verifica si el usuario es solicitante."""
        return await self.has_role(user_sub, UserRole.applicant)

    @staticmethod
    def create_pagination_meta(
        total: int,
        page: int,
        per_page: int,
    ) -> PaginationMeta:
        """Crea metadatos de paginación de forma consistente.

        Args:
            total: Número total de elementos
            page: Página actual (1-indexed)
            per_page: Elementos por página

        Returns:
            PaginationMeta: Metadatos calculados de paginación
        """
        pages = max((total + per_page - 1) // per_page, 1)
        return PaginationMeta(
            total=total,
            page=page,
            per_page=per_page,
            pages=pages,
            has_next=page < pages,
            has_prev=page > 1,
        )
