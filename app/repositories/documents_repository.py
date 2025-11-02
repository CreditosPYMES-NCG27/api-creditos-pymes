from datetime import datetime
from typing import Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import desc, func, select

from app.core.enums import DocumentStatus, SignatureStatus
from app.models.document import Document


class DocumentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, document_id: UUID) -> Document | None:
        result = await self.session.execute(
            select(Document).where(Document.id == document_id)
        )
        return result.scalars().first()

    async def get_by_storage_path(self, storage_path: str) -> Document | None:
        result = await self.session.execute(
            select(Document).where(Document.storage_path == storage_path)
        )
        return result.scalars().first()

    async def get_by_signature_request_id(
        self, signature_request_id: str
    ) -> Document | None:
        result = await self.session.execute(
            select(Document).where(
                Document.signature_request_id == signature_request_id
            )
        )
        return result.scalars().first()

    async def list_by_user(
        self,
        user_id: UUID,
        *,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[Sequence[Document], int]:
        offset = (page - 1) * limit
        query = (
            select(Document)
            .where(Document.user_id == user_id)
            .order_by(desc(Document.created_at))
        )

        total = (
            await self.session.execute(
                select(func.count())
                .select_from(Document)
                .where(Document.user_id == user_id)
            )
        ).scalar_one()

        items = (
            (await self.session.execute(query.offset(offset).limit(limit)))
            .scalars()
            .all()
        )

        return items, total

    async def list_by_application(
        self,
        application_id: UUID,
        *,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[Sequence[Document], int]:
        offset = (page - 1) * limit
        query = (
            select(Document)
            .where(Document.application_id == application_id)
            .order_by(desc(Document.created_at))
        )

        total = (
            await self.session.execute(
                select(func.count())
                .select_from(Document)
                .where(Document.application_id == application_id)
            )
        ).scalar_one()

        items = (
            (await self.session.execute(query.offset(offset).limit(limit)))
            .scalars()
            .all()
        )

        return items, total

    async def update_signature_status(
        self,
        document_id: UUID,
        signature_status: SignatureStatus,
        signature_request_id: str | None = None,
        signed_at: datetime | None = None,
        signed_file_path: str | None = None,
    ) -> Document | None:
        result = await self.session.execute(
            select(Document).where(Document.id == document_id)
        )
        document = result.scalars().first()
        if not document:
            return None

        document.signature_status = signature_status
        if signature_request_id:
            document.signature_request_id = signature_request_id
        if signed_at:
            document.signed_at = signed_at
        if signed_file_path:
            document.signed_file_path = signed_file_path

        await self.session.commit()
        await self.session.refresh(document)
        return document

    async def update_status(
        self,
        document_id: UUID,
        status: DocumentStatus,
    ) -> Document | None:
        """Actualiza el status de revisión de un documento.

        Args:
            document_id: ID del documento
            status: Nuevo estado (pending, approved, rejected)

        Returns:
            Document actualizado o None si no existe
        """
        result = await self.session.execute(
            select(Document).where(Document.id == document_id)
        )
        document = result.scalars().first()
        if not document:
            return None

        document.status = status
        await self.session.commit()
        await self.session.refresh(document)
        return document

    async def create_document(self, document: Document) -> Document:
        """Crea un nuevo registro de documento (placeholder o real)."""
        self.session.add(document)
        await self.session.commit()
        await self.session.refresh(document)
        return document
