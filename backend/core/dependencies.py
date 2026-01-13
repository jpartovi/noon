from __future__ import annotations

from datetime import datetime
from typing import Annotated

from schemas.user import AuthenticatedUser
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from domains.auth.repository import AuthRepository
from utils.errors import SupabaseAuthError

security = HTTPBearer()


async def get_current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> AuthenticatedUser:
    """
    Dependency to get the current authenticated user from the request.
    Validates the JWT token and returns the user information.
    Also stores user_id in request.state for middleware access.
    """
    token = credentials.credentials

    repository = AuthRepository()
    try:
        user = await repository.get_user_from_token(token)
    except SupabaseAuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    if not user or not user.get("id"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    # Store user_id in request.state for middleware logging
    request.state.user_id = user["id"]

    return AuthenticatedUser(
        id=user["id"],
        phone=user["phone"],
        created_at=user["created_at"],
        updated_at=user["updated_at"],
    )
