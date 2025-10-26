import hashlib
import hmac
import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request

from app.dependencies.auth import CurrentUserDep
from app.dependencies.services import DocumentServiceDep
from app.schemas.document import (
    DocumentResponse,
    SignatureRequest,
    SignatureResponse,
    SignatureStatusResponse,
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


@router.get(
    "/signatures/{signature_request_id}/status", response_model=SignatureStatusResponse
)
async def get_signature_status(
    signature_request_id: str,
    service: DocumentServiceDep,
    user: CurrentUserDep,
):
    """Consulta el estado de una signature request y descarga el PDF firmado si está completo."""
    return await service.get_signature_status(signature_request_id, user.sub)


# Webhook de HelloSign - NO requiere autenticación JWT
webhook_router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@webhook_router.post("/hellosign")
async def hellosign_webhook(request: Request, service: DocumentServiceDep):
    """Webhook para recibir eventos de HelloSign.

    HelloSign enviará eventos cuando:
    - signature_request_signed: Un firmante completó su firma
    - signature_request_all_signed: Todos los firmantes completaron
    - signature_request_declined: Un firmante rechazó firmar
    """
    # Leer body raw para validar HMAC
    body_bytes = await request.body()

    # Validar HMAC signature (seguridad)
    hellosign_signature = request.headers.get("x-hellosign-signature")
    if hellosign_signature:
        # Verificar firma HMAC con tu API key
        expected_signature = hmac.new(
            service.settings.hellosign_api_key.encode(),
            body_bytes,
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(hellosign_signature, expected_signature):
            raise HTTPException(status_code=401, detail="Invalid HMAC signature")

    # Parsear evento
    try:
        form_data = await request.form()
        event_json = form_data.get("json")
        if not event_json:
            raise HTTPException(status_code=400, detail="Missing json field")

        # event_json puede ser str o UploadFile
        event_json_str = str(event_json)

        event = json.loads(event_json_str)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error parsing webhook: {e}")

    event_type = event.get("event", {}).get("event_type")
    signature_request_id = event.get("signature_request", {}).get(
        "signature_request_id"
    )

    if not signature_request_id:
        return {"message": "Hello API Event Received (no signature_request_id)"}

    # Procesar eventos relevantes
    if event_type == "signature_request_all_signed":
        # Todos firmaron - descargar y guardar PDF
        await service.handle_signature_completed(signature_request_id)

    elif event_type == "signature_request_declined":
        # Alguien rechazó - marcar como rechazado
        await service.handle_signature_declined(signature_request_id)

    return {"message": "Hello API Event Received"}
