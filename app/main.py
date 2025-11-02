from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.bootstrap import app_lifespan
from app.config import get_settings
from app.exception_handlers import register_exception_handlers
from app.routers import companies, credit_applications, documents, metadata, profiles

app = FastAPI(
    title="API Créditos PyMEs",
    description="API para gestión de créditos a pequeñas y medianas empresas",
    version="0.1.0",
    lifespan=app_lifespan,
)

settings = get_settings()
app.state.settings = settings

if settings.environment == "production":
    if not settings.prod_domain:
        raise RuntimeError("PROD_DOMAIN debe estar configurado en production")
    allowed_origins = [settings.prod_domain]
else:
    allowed_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)


@app.get("/", tags=["root"])
async def read_root():
    """Endpoint raíz para verificar que la API está funcionando."""
    return {
        "name": app.title,
        "version": app.version,
        "docs": "/docs",
    }


@app.get("/health", tags=["health"])
async def health_check():
    """Endpoint para verificar la salud de la API."""
    return {"status": "healthy"}


# API v1
api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(profiles.router)
api_v1_router.include_router(companies.router)
api_v1_router.include_router(credit_applications.router)
api_v1_router.include_router(documents.router)
api_v1_router.include_router(metadata.router)
app.include_router(api_v1_router)
