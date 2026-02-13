"""
Optional Auth0 JWT validation for protecting routes.

Set AUTH0_DOMAIN and AUTH0_AUDIENCE in .env to enable. Then use
  Depends(get_current_user)
on any route that requires a valid Bearer token.
"""
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient
from pydantic import BaseModel

from api.config import AUTH0_AUDIENCE, AUTH0_DOMAIN, AUTH_ENABLED

security = HTTPBearer(auto_error=False)


class UserClaims(BaseModel):
    """Minimal claims from a validated JWT (Auth0)."""
    sub: str
    scope: str | None = None
    permissions: list[str] | None = None

    @property
    def user_id(self) -> str:
        return self.sub


def _get_jwks_client() -> PyJWKClient:
    if not AUTH_ENABLED:
        raise RuntimeError("Auth not configured (set AUTH0_DOMAIN and AUTH0_AUDIENCE)")
    url = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"
    return PyJWKClient(url)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
) -> UserClaims:
    """Validate Bearer JWT and return claims. Use as Depends(get_current_user) on protected routes."""
    if not AUTH_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Auth not configured. Set AUTH0_DOMAIN and AUTH0_AUDIENCE.",
        )
    if not credentials or credentials.credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = credentials.credentials
    try:
        jwks_client = _get_jwks_client()
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=AUTH0_AUDIENCE,
            issuer=f"https://{AUTH0_DOMAIN}/",
        )
        return UserClaims(
            sub=payload.get("sub", ""),
            scope=payload.get("scope"),
            permissions=payload.get("permissions"),
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user_optional(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
) -> UserClaims | None:
    """Same as get_current_user but returns None when no/invalid token (for optional auth)."""
    if not AUTH_ENABLED:
        return None
    if not credentials or not credentials.credentials:
        return None
    try:
        return get_current_user(credentials)
    except HTTPException:
        return None


def get_current_user_or_dev(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
) -> UserClaims:
    """Auth when configured; otherwise return dev user for local development."""
    if not AUTH_ENABLED:
        return UserClaims(sub="local-dev-user")
    return get_current_user(credentials)
