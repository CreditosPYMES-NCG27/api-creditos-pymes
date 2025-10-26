from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.bootstrap import app_lifespan
from app.exception_handlers import register_exception_handlers
from app.routers import companies, credit_applications, metadata, profiles

app = FastAPI(
    title="API Créditos PyMEs",
    description="API para gestión de créditos a pequeñas y medianas empresas",
    version="0.1.0",
    lifespan=app_lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://automatic-adventure-4xvwg6r644xcj96w-5173.app.github.dev"
    ],  # your frontend Codespace URL
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
api_v1_router.include_router(metadata.router)
app.include_router(api_v1_router)
