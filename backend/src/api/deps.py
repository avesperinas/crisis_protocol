"""FastAPI shared dependencies."""

from collections.abc import AsyncIterator
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.ai.client import ClaudeClient
from src.config import settings
from src.db import async_session
from src.models import User
from src.services.ai_service import AIService
from src.services.auth_service import decode_access_token, get_user_by_id


async def get_session() -> AsyncIterator[AsyncSession]:
    async with async_session() as s:
        yield s


_bearer_required = HTTPBearer(auto_error=True)
_bearer_optional = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer_required)],
    session: AsyncSession = Depends(get_session),
) -> User:
    try:
        user_id = decode_access_token(credentials.credentials)
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=401, detail="invalid or expired token") from e
    user = await get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="user not found")
    return user


async def get_current_user_optional(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_optional)],
    session: AsyncSession = Depends(get_session),
) -> User | None:
    if not credentials:
        return None
    try:
        user_id = decode_access_token(credentials.credentials)
    except jwt.PyJWTError:
        return None
    return await get_user_by_id(session, user_id)


# Single shared AIService instance for the process. ClaudeClient is async-safe.
_ai_service: AIService | None = None


def get_ai_service() -> AIService:
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService(
            ClaudeClient(api_key=settings.anthropic_api_key or "missing"),
            haiku_only=settings.haiku_only,
        )
    return _ai_service


def set_ai_service(service: AIService) -> None:
    """Test hook: inject a mock service."""
    global _ai_service
    _ai_service = service
