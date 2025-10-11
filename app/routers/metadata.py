import hashlib
import json

from fastapi import APIRouter, Request, Response

from app.schemas.credit_application import CreditPurpose, PURPOSE_LABELS


router = APIRouter(prefix="/metadata", tags=["metadata"])


@router.get("/credit-purposes")
async def list_credit_purposes(request: Request) -> Response:
    """Listado de propósitos válidos para el frontend (MVP).

    Incluye cabeceras HTTP de caché: ETag y Cache-Control.
    """
    payload = [
        {"code": purpose.value, "label": PURPOSE_LABELS[purpose]}
        for purpose in sorted(CreditPurpose, key=lambda p: p.value)
    ]

    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    etag = '"' + hashlib.md5(body.encode("utf-8")).hexdigest() + '"'

    if request.headers.get("if-none-match") == etag:
        return Response(status_code=304)

    resp = Response(content=body, media_type="application/json")
    resp.headers["ETag"] = etag
    resp.headers["Cache-Control"] = "public, max-age=3600, stale-while-revalidate=60"
    return resp
