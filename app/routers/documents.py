from uuid import UUID

from fastapi import APIRouter, Depends

from app.dependencies.auth import CurrentUserDep
from app.dependencies.services import DocumentServiceDep
from app.schemas.document import (
    DocumentResponse,
    DocumentUpdate,
    SignatureRequest,
    SignatureResponse,
)
from app.schemas.pagination import Paginated, PaginatedParams, pagination_params

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("/", response_model=Paginated[DocumentResponse])
async def list_documents(
    service: DocumentServiceDep,
    user: CurrentUserDep,
    params: PaginatedParams = Depends(pagination_params),
    application_id: UUID | None = None,
):
    """Lista documentos del usuario autenticado con paginación.

    Admin/operator pueden ver todos los documentos filtrando por application_id.
    Applicant solo ve sus propios documentos.
    """
    return await service.list_documents(
        user_sub=user.sub,
        page=params.page,
        limit=params.limit,
        application_id=application_id,
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    service: DocumentServiceDep,
    document_id: UUID,
    user: CurrentUserDep,
):
    """Obtiene un documento por ID.

    Admin/operator pueden ver cualquier documento.
    Applicant solo puede ver sus propios documentos.
    """
    return await service.get_document(document_id=document_id, user_sub=user.sub)


@router.post("/{document_id}/sign", response_model=SignatureResponse)
async def sign_document(
    service: DocumentServiceDep,
    document_id: UUID,
    signature_request: SignatureRequest,
    user: CurrentUserDep,
):
    """Inicia el proceso de firma embebida usando HelloSign.

    Crea una Signature Request embebida y retorna la URL de firma.
    Solo el dueño del documento o admin/operator pueden solicitar la firma.
    """
    return await service.create_signature_request(
        document_id=document_id,
        signature_request=signature_request,
        user_sub=user.sub,
    )


@router.patch("/{document_id}", response_model=DocumentResponse)
async def update_document_status(
    service: DocumentServiceDep,
    document_id: UUID,
    document_update: DocumentUpdate,
    user: CurrentUserDep,
):
    """Actualiza el status de revisión de un documento (solo admin/operator).

    Permite cambiar el estado de un documento entre: approved, rejected.
    Nota: "uploaded" lo establece el sistema cuando el usuario sube el archivo.
    Solo usuarios con rol admin u operator pueden actualizar el status.
    """
    return await service.update_document_status(
        document_id=document_id,
        status=document_update.status,
        user_sub=user.sub,
    )
