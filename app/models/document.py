from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import TIMESTAMP
from sqlmodel import JSON, Column, Enum, Field, ForeignKeyConstraint, SQLModel, func

from app.core.enums import DocumentStatus, DocumentType, SignatureStatus


class Document(SQLModel, table=True):
    """Modelo de documento subido a storage (auto-populado por trigger)"""

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        index=True,
        sa_column_kwargs={"server_default": func.gen_random_uuid()},
    )
    user_id: UUID = Field(nullable=False, index=True)
    application_id: UUID | None = Field(default=None, index=True)

    # Info desde storage.objects
    # Permitir NULL para permitir registros "request" (placeholders) antes de que el
    # archivo sea subido y el trigger complete los campos reales.
    storage_path: str | None = Field(
        default=None, nullable=True, unique=True, index=True
    )
    bucket_name: str | None = Field(default=None, max_length=100, nullable=True)
    file_name: str | None = Field(default=None, max_length=255, nullable=True)
    file_size: int | None = Field(default=None, ge=0)
    mime_type: str | None = Field(default=None, max_length=100)

    # Metadata adicional
    document_type: DocumentType | None = Field(
        default=None,
        sa_column=Column(
            Enum(
                DocumentType,
                name="document_type",
                native_enum=True,
                create_type=False,
            ),
            nullable=True,
        ),
    )
    status: DocumentStatus = Field(
        default=DocumentStatus.pending,
        sa_column=Column(
            Enum(
                DocumentStatus,
                name="document_status",
                native_enum=True,
                create_type=False,
            ),
            nullable=False,
            server_default="pending",
        ),
    )
    extra_metadata: dict[str, Any] | None = Field(
        default=None,
        sa_type=JSON,
    )

    # Firma digital
    signature_request_id: str | None = Field(default=None, max_length=255)
    signature_status: SignatureStatus = Field(
        default=SignatureStatus.unsigned,
        sa_column=Column(
            Enum(
                SignatureStatus,
                name="signature_status",
                native_enum=True,
                create_type=False,
            ),
            nullable=False,
            server_default="unsigned",
        ),
    )
    signed_at: datetime | None = Field(
        default=None,
        sa_column=Column(TIMESTAMP(timezone=True), nullable=True),
    )
    signed_file_path: str | None = Field(default=None)

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(
            TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
        ),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=func.now(),
            onupdate=func.now(),
        ),
    )

    __tablename__ = "documents"  # type: ignore[assignment]
    __table_args__ = (
        ForeignKeyConstraint(
            ["user_id"],
            ["profiles.id"],
            name="fk_documents_user",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["application_id"],
            ["credit_applications.id"],
            name="fk_documents_application",
            ondelete="CASCADE",
        ),
    )
