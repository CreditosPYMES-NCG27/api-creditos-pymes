from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.schemas.auth import Principal

BearerToken = Annotated[HTTPAuthorizationCredentials, Security(HTTPBearer())]


async def get_jwt_payload(request: Request, creds: BearerToken) -> dict:
    """Decodifica y valida el JWT del usuario autenticado."""
    token = creds.credentials
    jwks_client: jwt.PyJWKClient = request.app.state.jwks_client
    try:
        key = jwks_client.get_signing_key_from_jwt(token).key
        issuer = f"{request.app.state.settings.project_url}/auth/v1"
        payload = jwt.decode(
            token, key, ["ES256"], audience="authenticated", issuer=issuer
        )
        return payload
    except jwt.ExpiredSignatureError as err:
        raise HTTPException(status_code=401, detail="Expired token") from err
    except jwt.InvalidAudienceError as err:
        raise HTTPException(status_code=401, detail="Invalid token audience") from err
    except jwt.InvalidIssuerError as err:
        raise HTTPException(status_code=401, detail="Invalid token issuer") from err
    except jwt.InvalidTokenError as err:
        raise HTTPException(status_code=401, detail="Invalid token") from err


JWTPayload = Annotated[dict, Depends(get_jwt_payload)]


async def get_current_user(payload: JWTPayload) -> Principal:
    """Extrae el `Principal` del payload ya validado."""
    sub = payload.get("sub")
    email = payload.get("email")
    if not sub:
        raise HTTPException(status_code=401, detail="Token no contiene user_id (sub)")
    return Principal(sub=sub, email=email)


CurrentUserDep = Annotated[Principal, Depends(get_current_user)]
