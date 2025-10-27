from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.enums import DocumentStatus, DocumentType, SignatureStatus


class DocumentResponse(BaseModel):
    """Schema de respuesta para documento"""

    id: Annotated[UUID, Field(description="ID único del documento")]
    user_id: Annotated[UUID, Field(description="ID del usuario que subió")]
    application_id: Annotated[
        UUID | None, Field(description="ID de solicitud asociada (opcional)")
    ]
    storage_path: Annotated[str, Field(description="Ruta en storage")]
    bucket_name: Annotated[str, Field(description="Bucket de storage")]
    file_name: Annotated[str, Field(description="Nombre del archivo")]
    file_size: Annotated[int | None, Field(description="Tamaño en bytes")]
    mime_type: Annotated[str | None, Field(description="Tipo MIME")]
    document_type: Annotated[
        DocumentType | None, Field(description="Tipo de documento")
    ]
    status: Annotated[
        DocumentStatus,
        Field(description="Estado de revisión: pending, approved, rejected, expired"),
    ]
    signature_status: Annotated[SignatureStatus, Field(description="Estado de firma")]
    signature_request_id: Annotated[
        str | None, Field(description="ID de solicitud de firma")
    ]
    signed_at: Annotated[datetime | None, Field(description="Fecha de firma")]
    signed_file_path: Annotated[
        str | None, Field(description="Ruta del archivo firmado")
    ]
    created_at: Annotated[datetime, Field(description="Fecha de creación")]
    updated_at: Annotated[datetime, Field(description="Fecha de actualización")]


class SignatureRequest(BaseModel):
    """Schema para solicitar firma de documento"""

    signer_email: Annotated[str, Field(description="Email del firmante")]
    signer_name: Annotated[str, Field(description="Nombre del firmante")]
    callback_url: Annotated[
        str | None, Field(None, description="URL de callback al completar firma")
    ]


class SignatureResponse(BaseModel):
    """Schema de respuesta al iniciar proceso de firma"""

    signature_request_id: Annotated[str, Field(description="ID de solicitud de firma")]
    signing_url: Annotated[str, Field(description="URL para firmar (iframe/redirect)")]
    expires_at: Annotated[datetime | None, Field(description="Expiración de la URL")]


class SignatureStatusResponse(BaseModel):
    """Estado de una solicitud de firma en el proveedor"""

    signature_request_id: Annotated[str, Field(description="ID de la solicitud")]
    status_code: Annotated[
        str, Field(description="Estado: pending, complete, declined, canceled, etc.")
    ]


class DocumentUpdate(BaseModel):
    """Schema para actualizar status de documento (solo admin/operator)"""

    status: Annotated[
        DocumentStatus,
        Field(description="Nuevo estado: pending, approved, rejected, expired"),
    ]
