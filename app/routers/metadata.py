from typing import Sequence

from fastapi import APIRouter

from app.core.enums import CreditApplicationPurpose
from app.schemas.credit_application import (
    CreditPurposeResponse,
)

router = APIRouter(prefix="/metadata", tags=["metadata"])


CREDIT_PURPOSES_LABELS = {
    CreditApplicationPurpose.working_capital: "Capital de trabajo",
    CreditApplicationPurpose.equipment: "Compra de equipo",
    CreditApplicationPurpose.expansion: "Expansión",
    CreditApplicationPurpose.inventory: "Inventario",
    CreditApplicationPurpose.refinancing: "Refinanciamiento",
    CreditApplicationPurpose.other: "Otro",
}


@router.get("/credit-purposes", response_model=Sequence[CreditPurposeResponse])
async def list_credit_purposes():
    """Listado de propósitos de crédito válidos para el frontend."""
    return [
        CreditPurposeResponse(value=i, slug=p.name, label=CREDIT_PURPOSES_LABELS[p])
        for i, p in enumerate(CreditApplicationPurpose)
    ]
