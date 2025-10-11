from fastapi import APIRouter, FastAPI

from app.routers import companies, profiles

app = FastAPI(
    title="API Créditos PyMEs",
    description="API para gestión de créditos a pequeñas y medianas empresas",
    version="0.1.0",
)


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
app.include_router(api_v1_router)
