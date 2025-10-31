from contextlib import asynccontextmanager

from fastapi import FastAPI
from jwt import PyJWKClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlmodel import SQLModel

from app.config import get_settings


@asynccontextmanager
async def app_lifespan(app: FastAPI):
    """Inicializa recursos compartidos por la app, como el motor de base de datos y el JWKS client.
    Estos recursos se almacenan en `app.state` para que estén disponibles en los endpoints y dependencias.
    """
    app.state.settings = get_settings()

    app.state.jwks_client = PyJWKClient(
        f"{app.state.settings.project_url}/auth/v1/.well-known/jwks.json",
        cache_keys=True,
        max_cached_keys=2,
        lifespan=3600,
    )

    db_user = app.state.settings.db_user
    db_pass = app.state.settings.db_pass
    db_name = app.state.settings.db_name
    db_host = app.state.settings.db_host
    db_port = app.state.settings.db_port
    database_url = (
        f"postgresql+asyncpg://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    )

    engine = create_async_engine(
        database_url,
        pool_size=20,         
        max_overflow=10, 
        pool_pre_ping=True,
        pool_recycle=1800,
        echo=False,
    )
    app.state.async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    try:
        yield
    except Exception as e:
        print(f"Error en lifespan: {e}")
        raise
    finally:
        if "engine" in locals():
            await engine.dispose()
