"""Servicio de documentos con workflow de firma digital (HelloSign)"""

from datetime import datetime, timedelta, timezone
from uuid import UUID

import httpx
from dropbox_sign.api.embedded_api import EmbeddedApi
from dropbox_sign.api.signature_request_api import SignatureRequestApi
from dropbox_sign.api_client import ApiClient
from dropbox_sign.configuration import Configuration
from dropbox_sign.models.signature_request_create_embedded_request import (
    SignatureRequestCreateEmbeddedRequest,
)
from dropbox_sign.models.sub_signature_request_signer import (
    SubSignatureRequestSigner,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.core.enums import DocumentStatus, DocumentType, SignatureStatus, UserRole
from app.core.errors import ForbiddenError, NotFoundError, ValidationDomainError
from app.models.document import Document
from app.repositories.documents_repository import DocumentRepository
from app.repositories.protocols import DocumentRepositoryProtocol
from app.schemas.document import (
    DocumentResponse,
    SignatureRequest,
    SignatureResponse,
)
from app.schemas.pagination import Paginated
from app.services.base_service import BaseService


class DocumentService(BaseService):
    """Servicio para gestionar documentos y workflow de firma digital con HelloSign"""

    def __init__(
        self,
        session: AsyncSession,
        settings: Settings,
        document_repo: DocumentRepositoryProtocol | None = None,
    ):
        super().__init__(session)
        self.settings = settings
        self.document_repo = document_repo or DocumentRepository(session)

    async def get_document(self, document_id: UUID, user_sub: str) -> DocumentResponse:
        """Obtiene un documento por ID con verificación de permisos.

        Args:
            document_id: ID del documento
            user_sub: ID del usuario autenticado

        Returns:
            DocumentResponse: Documento encontrado

        Raises:
            NotFoundError: Si el documento no existe
            ForbiddenError: Si el usuario no tiene acceso al documento
        """
        document = await self.document_repo.get_by_id(document_id)
        if not document:
            raise NotFoundError("Documento no encontrado")

        # Verificar permisos: admin/operator puede ver todo, applicant solo sus documentos
        user_role = await self.assert_role(user_sub)
        if user_role == UserRole.applicant and document.user_id != UUID(user_sub):
            raise ForbiddenError("No tiene acceso a este documento")

        return DocumentResponse.model_validate(document, from_attributes=True)

    async def list_documents(
        self,
        user_sub: str,
        page: int = 1,
        limit: int = 20,
        application_id: UUID | None = None,
    ) -> Paginated[DocumentResponse]:
        """Lista documentos con paginación y filtros.

        Args:
            user_sub: ID del usuario autenticado
            page: Número de página (1-indexed)
            limit: Elementos por página
            application_id: Filtrar por solicitud de crédito (opcional)

        Returns:
            Paginated[DocumentResponse]: Documentos paginados
        """
        user_role = await self.assert_role(user_sub)

        # Admin/operator pueden ver todos, applicant solo sus documentos
        if user_role in (UserRole.admin, UserRole.operator):
            if application_id:
                documents, total = await self.document_repo.list_by_application(
                    application_id, page=page, limit=limit
                )
            else:
                # Si se necesita listar todos sin filtro, se puede agregar un método list_all
                # Por ahora, requerimos application_id para admin/operator
                raise ValidationDomainError("Debe especificar application_id")
        else:
            user_uuid = UUID(user_sub)
            if application_id:
                documents, total = await self.document_repo.list_by_application(
                    application_id, page=page, limit=limit
                )
                # Verificar que todos los documentos pertenecen al usuario
                if documents and any(doc.user_id != user_uuid for doc in documents):
                    raise ForbiddenError("No tiene acceso a estos documentos")
            else:
                documents, total = await self.document_repo.list_by_user(
                    user_uuid, page=page, limit=limit
                )

        items = [
            DocumentResponse.model_validate(doc, from_attributes=True)
            for doc in documents
        ]
        meta = self.create_pagination_meta(total, page, limit)

        return Paginated(items=items, meta=meta)

    async def create_signature_request(
        self,
        document_id: UUID,
        signature_request: SignatureRequest,
        user_sub: str,
    ) -> SignatureResponse:
        """Crea una solicitud de firma embebida en HelloSign.

        Args:
            document_id: ID del documento a firmar
            signature_request: Datos del firmante
            user_sub: ID del usuario autenticado

        Returns:
            SignatureResponse: URL de firma embebida y datos de la solicitud

        Raises:
            NotFoundError: Si el documento no existe
            ForbiddenError: Si el usuario no tiene acceso o el documento ya está firmado
            ValidationError: Si hay errores en la integración con HelloSign
        """
        document = await self.document_repo.get_by_id(document_id)
        if not document:
            raise NotFoundError("Documento no encontrado")

        # Verificar permisos: solo el dueño o admin/operator pueden solicitar firma
        user_role = await self.assert_role(user_sub)
        if user_role == UserRole.applicant and document.user_id != UUID(user_sub):
            raise ForbiddenError("No tiene acceso a este documento")

        # Verificar que el documento no esté ya firmado
        if document.signature_status == SignatureStatus.signed:
            raise ForbiddenError("El documento ya está firmado")

        # Obtener URL del documento desde Supabase Storage
        if document.storage_path is None or document.bucket_name is None:
            raise ValidationDomainError(
                "El documento no tiene ruta de almacenamiento válida"
            )

        document_url = self._get_storage_signed_url(
            document.storage_path, document.bucket_name
        )

        # Crear Signature Request embebida en HelloSign
        signing_url = ""
        expires_at: datetime | None = None
        signature_request_id = ""
        try:
            configuration = Configuration(username=self.settings.hellosign_api_key)
            with ApiClient(configuration) as api_client:
                sig_api = SignatureRequestApi(api_client)
                emb_api = EmbeddedApi(api_client)

                req = SignatureRequestCreateEmbeddedRequest(
                    client_id=self.settings.hellosign_client_id,
                    test_mode=True,
                    subject=f"Firma requerida: {document.file_name}",
                    message=f"Por favor firme el documento: {document.file_name}",
                    signers=[
                        SubSignatureRequestSigner(
                            email_address=signature_request.signer_email,
                            name=signature_request.signer_name,
                        )
                    ],
                    file_urls=[document_url],
                )

                create_res = sig_api.signature_request_create_embedded(req)
                sr = create_res.signature_request
                signature_request_id = sr.signature_request_id or ""
                # Obtener el primer signature_id para la URL embebida
                signature_id = (
                    sr.signatures[0].signature_id
                    if sr.signatures and len(sr.signatures) > 0
                    else None
                )

                if not signature_id:
                    raise ValidationDomainError("HelloSign no devolvió signature_id")

                emb_res = emb_api.embedded_sign_url(signature_id)
                signing_url = emb_res.embedded.sign_url or ""

                # Agregar client_id y skip_domain_verification para test_mode
                if signing_url:
                    separator = "&" if "?" in signing_url else "?"
                    if "client_id" not in signing_url:
                        signing_url = f"{signing_url}{separator}client_id={self.settings.hellosign_client_id}"
                        separator = "&"
                    # En test_mode, agregar skip_domain_verification
                    if "skip_domain_verification" not in signing_url:
                        signing_url = (
                            f"{signing_url}{separator}skip_domain_verification=1"
                        )

                exp_val = getattr(emb_res.embedded, "expires_at", None)
                if exp_val is not None:
                    expires_at = datetime.fromtimestamp(float(exp_val), tz=timezone.utc)
                else:
                    expires_at = None
        except Exception as e:
            raise ValidationDomainError(
                f"Error creando solicitud de firma en HelloSign: {e}"
            )

        # Actualizar documento con signature_request_id y estado pending
        await self.document_repo.update_signature_status(
            document_id=document_id,
            signature_request_id=signature_request_id,
            signature_status=SignatureStatus.pending,
        )

        # HelloSign controla la expiración de la URL retornada; si no viene, estimar 1 hora
        expires_at = expires_at or (datetime.now(timezone.utc) + timedelta(hours=1))
        return SignatureResponse(
            signature_request_id=signature_request_id,
            signing_url=signing_url,
            expires_at=expires_at,
        )

    def _get_storage_signed_url(self, storage_path: str, bucket_name: str) -> str:
        """Genera URL firmada temporal para acceder al documento en Supabase Storage.

        Args:
            storage_path: Ruta del archivo en storage
            bucket_name: Nombre del bucket

        Returns:
            str: URL firmada temporal (válida por 1 hora)
        """
        # Usar Supabase Storage API para generar signed URL
        # Esto requiere el service key para operaciones privilegiadas
        url = f"{self.settings.project_url}/storage/v1/object/sign/{bucket_name}/{storage_path}"

        try:
            with httpx.Client() as client:
                response = client.post(
                    url,
                    json={"expiresIn": 3600},  # 1 hora
                    headers={
                        "Authorization": f"Bearer {self.settings.supabase_service_key}",
                        "apikey": self.settings.supabase_service_key,
                    },
                )
                response.raise_for_status()
                signed_url = response.json()["signedURL"]
                # La URL firmada es relativa, construir URL completa
                return f"{self.settings.project_url}/storage/v1{signed_url}"
        except httpx.HTTPError as e:
            raise ValidationDomainError(f"Error generando URL firmada: {e}")

    async def update_document_status(
        self,
        document_id: UUID,
        status: DocumentStatus,
        user_sub: str,
    ) -> DocumentResponse:
        """Actualiza el status de un documento (solo admin/operator).

        Args:
            document_id: ID del documento
            status: Nuevo estado (pending, approved, rejected)
            user_sub: ID del usuario autenticado

        Returns:
            DocumentResponse: Documento actualizado

        Raises:
            NotFoundError: Si el documento no existe
            ForbiddenError: Si el usuario no tiene permisos (debe ser admin/operator)
        """
        # Verificar permisos: solo admin/operator pueden cambiar status
        user_role = await self.assert_role(user_sub)
        if user_role not in (UserRole.admin, UserRole.operator):
            raise ForbiddenError(
                "Solo administradores y operadores pueden actualizar el estado del documento"
            )

        # Actualizar status
        document = await self.document_repo.update_status(
            document_id=document_id,
            status=status,
        )
        if not document:
            raise NotFoundError("Documento no encontrado")

        return DocumentResponse.model_validate(document, from_attributes=True)

    async def request_document(
        self,
        user_sub: str,
        application_id: UUID | None = None,
        document_type: DocumentType | None = None,
        notes: str | None = None,
    ) -> DocumentResponse:
        """Crea un placeholder de documento solicitado por un operador/admin.

        Los campos de storage permanecen NULL hasta que el usuario suba el archivo
        y el trigger/función complete los metadatos.
        """
        # Solo operadores/admins pueden solicitar documentos
        user_role = await self.assert_role(user_sub)
        if user_role not in (UserRole.admin, UserRole.operator):
            raise ForbiddenError(
                "Solo administradores y operadores pueden solicitar documentos"
            )

        # Crear modelo Document con campos de storage en NULL
        from uuid import UUID as _UUID

        doc = Document(
            user_id=_UUID(user_sub),
            application_id=application_id,
            document_type=document_type,
            storage_path=None,
            bucket_name=None,
            file_name=None,
            status=DocumentStatus.requested,
            extra_metadata={
                "requested_by": str(user_sub),
                "notes": notes,
            },
        )

        created = await self.document_repo.create_document(doc)
        return DocumentResponse.model_validate(created, from_attributes=True)
