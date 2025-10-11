import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient
from supabase import AsyncClient, acreate_client

from app.config import Settings

bearer = HTTPBearer()
settings = Settings()


def get_jwks_client():
    return PyJWKClient(f"{settings.project_url}/auth/v1/.well-known/jwks.json")


def verify_jwt_token(token: str) -> dict:
    """
    Verifica y decodifica un token JWT usando las claves JWKS de Supabase.

    Seguridad:
    - Valida el token JWT usando JWKS (ES256)
    - Verifica firma con llaves públicas de Supabase
    - Verifica expiración y audiencia del token

    :param token: El token JWT a verificar
    :type token: str
    :return: El payload del token JWT
    :rtype: dict[str, Any]
    :raises HTTPException: Si el token es inválido o ha expirado
    """
    try:
        jwks = get_jwks_client()
        signing_key = jwks.get_signing_key_from_jwt(token).key

        payload = jwt.decode(
            jwt=token,
            key=signing_key,
            algorithms=["ES256"],
            audience="authenticated",
            issuer=f"{settings.project_url}/auth/v1",
            options={
                "verify_aud": True,
                "verify_exp": True,
                "verify_signature": True,
            },
        )
        return payload
    except jwt.ExpiredSignatureError as err:
        raise HTTPException(status_code=401, detail="Token expirado") from err
    except jwt.InvalidAudienceError as err:
        raise HTTPException(status_code=401, detail="Audiencia inválida") from err
    except jwt.InvalidIssuerError as err:
        raise HTTPException(status_code=401, detail="Issuer inválido") from err
    except jwt.InvalidTokenError as err:
        raise HTTPException(status_code=401, detail="Token inválido") from err


async def get_jwt_payload(
    creds: HTTPAuthorizationCredentials = Depends(bearer),
) -> dict:
    """
    Extrae y verifica el payload del token JWT de las credenciales HTTP.

    :param creds: Credenciales de autorización HTTP
    :type creds: HTTPAuthorizationCredentials
    :return: El payload del token JWT
    :rtype: dict
    """
    token = creds.credentials
    return verify_jwt_token(token)


async def get_current_user_id(
    creds: HTTPAuthorizationCredentials = Depends(bearer),
) -> str:
    """
    Extrae el user_id (sub) del token JWT del usuario autenticado.

    :param creds: Credenciales de autorización HTTP
    :type creds: HTTPAuthorizationCredentials
    :return: El user_id (sub) del usuario autenticado
    :rtype: str
    :raise HTTPException: Si el token no contiene user_id (sub)
    """
    token = creds.credentials
    payload = verify_jwt_token(token)

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Token no contiene user_id (sub)")

    return user_id


async def supabase_for_user(
    payload: dict = Depends(get_jwt_payload),
    creds: HTTPAuthorizationCredentials = Depends(bearer),
) -> AsyncClient:
    """
    Provee un cliente de Supabase autenticado con el JWT del usuario.

    :param payload: Payload verificado del token JWT
    :type payload: dict
    :param creds: Credenciales de autorización HTTP
    :type creds: HTTPAuthorizationCredentials
    :return: Cliente de Supabase autenticado
    :rtype: AsyncClient
    """
    token = creds.credentials

    client = await acreate_client(settings.project_url, settings.publishable_key)
    client.postgrest.auth(token)

    return client


async def supabase_for_admin() -> AsyncClient:
    """
    Provee un cliente de Supabase con privilegios de administrador (bypass RLS).

    :return: Cliente de Supabase con privilegios de administrador
    :rtype: AsyncClient
    """
    client = await acreate_client(settings.project_url, settings.secret_key)
    return client
