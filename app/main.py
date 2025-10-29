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

# Configurar CORS
settings = get_settings()

# Lista base de orígenes permitidos para desarrollo local
allowed_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

# Agregar dominio de producción si está configurado y en modo producción
if settings.environment == "production" and settings.prod_domain:
    allowed_origins.append(settings.prod_domain)

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
