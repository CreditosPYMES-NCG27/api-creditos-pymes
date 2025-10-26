"""Servicio de documentos con workflow de firma digital (HelloSign)"""

from datetime import datetime, timedelta, timezone
from pathlib import Path
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
from app.core.enums import SignatureStatus, UserRole
from app.core.errors import ForbiddenError, NotFoundError, ValidationDomainError
from app.repositories.documents_repository import DocumentRepository
from app.repositories.protocols import DocumentRepositoryProtocol
from app.schemas.document import (
    DocumentResponse,
    SignatureRequest,
    SignatureResponse,
    SignatureStatusResponse,
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

    async def get_signature_status(
        self, signature_request_id: str, user_sub: str
    ) -> SignatureStatusResponse:
        """Consulta el estado de una signature request en HelloSign y descarga el PDF si está completo."""
        # Permisos: admin/operator pueden consultar cualquier, applicant solo los suyos
        document = await self.document_repo.get_by_signature_request_id(
            signature_request_id
        )
        if not document:
            raise NotFoundError("Documento no encontrado para esa signature request")

        user_role = await self.assert_role(user_sub)
        if user_role == UserRole.applicant and document.user_id != UUID(user_sub):
            raise ForbiddenError("No tiene acceso a esta signature request")

        try:
            configuration = Configuration(username=self.settings.hellosign_api_key)
            with ApiClient(configuration) as api_client:
                sig_api = SignatureRequestApi(api_client)
                res = sig_api.signature_request_get(signature_request_id)
                sr = res.signature_request
                # Derivar status desde flags/signatures
                status_code: str
                if getattr(sr, "is_complete", False):
                    status_code = "complete"
                elif any(
                    getattr(s, "status_code", "") == "declined"
                    for s in (sr.signatures or [])
                ):
                    status_code = "declined"
                else:
                    status_code = "pending"

                # Si está completa, descargar y guardar PDF firmado
                if (
                    status_code == "complete"
                    and document.signature_status != SignatureStatus.signed
                ):
                    file_obj = sig_api.signature_request_files(
                        signature_request_id, file_type="pdf"
                    )
                    if hasattr(file_obj, "read"):
                        file_bytes = file_obj.read()
                    elif isinstance(file_obj, (bytes, bytearray)):
                        file_bytes = bytes(file_obj)
                    else:
                        raise ValidationDomainError(
                            "Respuesta de archivo de HelloSign no reconocida"
                        )
                    # Generar ruta para documento firmado
                    original_path = Path(document.storage_path)
                    signed_path_obj = (
                        original_path.parent
                        / f"{original_path.stem}_signed{original_path.suffix}"
                    )
                    # Convertir a formato POSIX (/) para Supabase Storage
                    signed_path = signed_path_obj.as_posix()

                    await self._upload_to_storage(
                        bucket_name=document.bucket_name,
                        file_path=signed_path,
                        file_content=file_bytes,
                        content_type=document.mime_type or "application/pdf",
                    )

                    await self.document_repo.update_signature_status(
                        document_id=document.id,
                        signature_status=SignatureStatus.signed,
                        signed_at=datetime.now(timezone.utc),
                        signed_file_path=signed_path,
                    )

                return SignatureStatusResponse(
                    signature_request_id=signature_request_id, status_code=status_code
                )
        except Exception as e:
            raise ValidationDomainError(f"Error consultando estado en HelloSign: {e}")

    async def handle_signature_completed(self, signature_request_id: str) -> None:
        """Procesa el evento de firma completada desde webhook de HelloSign.

        Args:
            signature_request_id: ID de la solicitud de firma
        """
        document = await self.document_repo.get_by_signature_request_id(
            signature_request_id
        )
        if not document:
            # Puede ser un evento de un documento que no está en nuestra DB
            return

        # Si ya está marcado como firmado, no hacer nada
        if document.signature_status == SignatureStatus.signed:
            return

        try:
            # Descargar PDF firmado
            configuration = Configuration(username=self.settings.hellosign_api_key)
            with ApiClient(configuration) as api_client:
                sig_api = SignatureRequestApi(api_client)
                file_obj = sig_api.signature_request_files(
                    signature_request_id, file_type="pdf"
                )

                if hasattr(file_obj, "read"):
                    file_bytes = file_obj.read()
                elif isinstance(file_obj, (bytes, bytearray)):
                    file_bytes = bytes(file_obj)
                else:
                    raise ValidationDomainError(
                        "Respuesta de archivo de HelloSign no reconocida"
                    )

            # Generar ruta para documento firmado
            original_path = Path(document.storage_path)
            signed_path_obj = (
                original_path.parent
                / f"{original_path.stem}_signed{original_path.suffix}"
            )
            # Convertir a formato POSIX (/) para Supabase Storage
            signed_path = signed_path_obj.as_posix()

            # Subir a storage
            await self._upload_to_storage(
                bucket_name=document.bucket_name,
                file_path=signed_path,
                file_content=file_bytes,
                content_type=document.mime_type or "application/pdf",
            )

            # Actualizar estado en DB
            await self.document_repo.update_signature_status(
                document_id=document.id,
                signature_status=SignatureStatus.signed,
                signed_at=datetime.now(timezone.utc),
                signed_file_path=signed_path,
            )

        except Exception as e:
            # Log error pero no fallar el webhook
            print(f"Error procesando firma completada: {e}")

    async def handle_signature_declined(self, signature_request_id: str) -> None:
        """Procesa el evento de firma rechazada desde webhook de HelloSign.

        Args:
            signature_request_id: ID de la solicitud de firma
        """
        document = await self.document_repo.get_by_signature_request_id(
            signature_request_id
        )
        if not document:
            return

        # Marcar como declined
        await self.document_repo.update_signature_status(
            document_id=document.id,
            signature_status=SignatureStatus.declined,
        )

    # DocuSign-specific helpers eliminados en migración a HelloSign

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

    # DocuSign envelope creation eliminado

    # Descarga de documento firmado manejada en get_signature_status para HelloSign

    async def _upload_to_storage(
        self,
        bucket_name: str,
        file_path: str,
        file_content: bytes,
        content_type: str,
    ) -> None:
        """Sube un archivo a Supabase Storage.

        Args:
            bucket_name: Nombre del bucket
            file_path: Ruta del archivo en storage
            file_content: Contenido del archivo
            content_type: MIME type del archivo

        Raises:
            ValidationError: Si hay errores subiendo el archivo
        """
        # Usar endpoint con upsert=true para permitir sobrescribir
        url = f"{self.settings.project_url}/storage/v1/object/{bucket_name}/{file_path}"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    content=file_content,
                    headers={
                        "Authorization": f"Bearer {self.settings.supabase_service_key}",
                        "apikey": self.settings.supabase_service_key,
                        "Content-Type": content_type,
                        "x-upsert": "true",  # Permitir sobrescribir si existe
                    },
                )
                response.raise_for_status()
        except httpx.HTTPError as e:
            raise ValidationDomainError(f"Error subiendo archivo a storage: {e}")
