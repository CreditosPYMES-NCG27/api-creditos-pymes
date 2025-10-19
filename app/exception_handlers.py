# app/errors.py
from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.errors import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ServiceError,
    UnauthorizedError,
    ValidationDomainError,
)


def register_exception_handlers(app):
    @app.exception_handler(NotFoundError)
    async def _404(_req: Request, exc: NotFoundError):
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(ConflictError)
    async def _409(_req: Request, exc: ConflictError):
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(UnauthorizedError)
    async def _401(_req: Request, exc: UnauthorizedError):
        return JSONResponse(status_code=401, content={"detail": str(exc)})

    @app.exception_handler(ForbiddenError)
    async def _403(_req: Request, exc: ForbiddenError):
        return JSONResponse(status_code=403, content={"detail": str(exc)})

    @app.exception_handler(ValidationDomainError)
    async def _400(_req: Request, exc: ValidationDomainError):
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    # catch-all opcional para evitar 500 no controlados
    @app.exception_handler(ServiceError)
    async def _500(_req: Request, exc: ServiceError):
        return JSONResponse(
            status_code=500, content={"detail": "internal service error"}
        )
