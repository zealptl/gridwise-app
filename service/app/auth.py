"""Cognito JWT Authentication Middleware"""

import logging
from typing import Optional

import httpx
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.config import settings

logger = logging.getLogger(__name__)

COGNITO_REGION = settings.AWS_REGION
COGNITO_USER_POOL_ID = settings.COGNITO_USER_POOL_ID
COGNITO_APP_CLIENT_ID = settings.COGNITO_APP_CLIENT_ID
AUTH_BYPASS = settings.AUTH_BYPASS

# Module-level JWKS cache: dict mapping kid -> key dict
_jwks_cache: dict = {}

if not COGNITO_USER_POOL_ID:
    if AUTH_BYPASS:
        logger.warning(
            "COGNITO_USER_POOL_ID is not set. AUTH_BYPASS=true — all auth checks will be skipped. "
            "Do NOT use this in production."
        )
    else:
        logger.warning(
            "COGNITO_USER_POOL_ID is not set. JWT validation will fail for all requests. "
            "Set AUTH_BYPASS=true to skip auth in local dev."
        )


def _cognito_issuer() -> str:
    return f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}"


def _jwks_url() -> str:
    return f"{_cognito_issuer()}/.well-known/jwks.json"


async def _fetch_jwks() -> dict:
    """Fetch JWKS from Cognito and return a dict mapping kid -> key dict."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(_jwks_url(), timeout=10.0)
        resp.raise_for_status()
        data = resp.json()
    return {key["kid"]: key for key in data.get("keys", [])}


async def _get_jwk(kid: str) -> Optional[dict]:
    """Return the JWK for a given kid, fetching/refreshing the cache as needed."""
    global _jwks_cache

    if kid in _jwks_cache:
        return _jwks_cache[kid]

    # Refresh cache once if kid not found
    _jwks_cache = await _fetch_jwks()
    return _jwks_cache.get(kid)


async def validate_token(token: str) -> str:
    """
    Validate a Cognito JWT and return the user_id (sub claim).

    Raises HTTPException(401) on any validation failure.
    """
    # Local dev bypass — never allow in production
    if AUTH_BYPASS and not COGNITO_USER_POOL_ID:
        logger.debug("AUTH_BYPASS active — skipping JWT validation")
        return "bypass-user"

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode the header without verification to extract kid
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        if not kid:
            raise credentials_exception

        # Retrieve the matching JWK
        jwk = await _get_jwk(kid)
        if not jwk is None and not jwk:
            raise credentials_exception
        if jwk is None:
            raise credentials_exception

        # Verify and decode the token
        issuer = _cognito_issuer()
        payload = jwt.decode(
            token,
            jwk,
            algorithms=["RS256"],
            audience=COGNITO_APP_CLIENT_ID,
            issuer=issuer,
            options={"verify_exp": True},
        )

        # Validate token_use claim
        token_use = payload.get("token_use")
        if token_use not in ("id", "access"):
            raise credentials_exception

        # Extract user ID from sub claim
        user_id: Optional[str] = payload.get("sub")
        if not user_id:
            raise credentials_exception

        return user_id

    except JWTError:
        raise credentials_exception
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unexpected error during JWT validation")
        raise credentials_exception


security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> str:
    """Validates JWT and returns user_id (Cognito sub claim)."""
    token = credentials.credentials
    return await validate_token(token)
