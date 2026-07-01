"""Auth endpoints: register, login, refresh, logout, me."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user, get_session
from src.models import User
from src.schemas.auth import (
    RefreshRequest,
    TokenResponse,
    UserLogin,
    UserProfile,
    UserRegister,
)
from src.services.auth_service import (
    AuthServiceError,
    InvalidCredentialsError,
    authenticate_user,
    create_access_token,
    create_session,
    register_user,
    revoke_session,
    rotate_session,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _to_profile(user: User) -> UserProfile:
    return UserProfile(
        id=user.id,
        email=user.email,
        username=user.username,
        locale=user.locale,
        created_at=user.created_at.isoformat(),
    )


@router.post("/register", response_model=TokenResponse)
async def register(
    payload: UserRegister, session: AsyncSession = Depends(get_session)
) -> TokenResponse:
    try:
        user = await register_user(
            session,
            email=payload.email,
            username=payload.username,
            password=payload.password,
            locale=payload.locale,
        )
    except AuthServiceError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    access_token = create_access_token(user.id)
    refresh_token = await create_session(session, user_id=user.id)
    return TokenResponse(
        access_token=access_token, refresh_token=refresh_token, user=_to_profile(user)
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: UserLogin, session: AsyncSession = Depends(get_session)
) -> TokenResponse:
    try:
        user = await authenticate_user(session, email=payload.email, password=payload.password)
    except InvalidCredentialsError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    access_token = create_access_token(user.id)
    refresh_token = await create_session(session, user_id=user.id)
    return TokenResponse(
        access_token=access_token, refresh_token=refresh_token, user=_to_profile(user)
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    payload: RefreshRequest, session: AsyncSession = Depends(get_session)
) -> TokenResponse:
    try:
        user, new_refresh_token = await rotate_session(
            session, refresh_token=payload.refresh_token
        )
    except InvalidCredentialsError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    access_token = create_access_token(user.id)
    return TokenResponse(
        access_token=access_token, refresh_token=new_refresh_token, user=_to_profile(user)
    )


@router.post("/logout")
async def logout(
    payload: RefreshRequest, session: AsyncSession = Depends(get_session)
) -> dict:
    await revoke_session(session, refresh_token=payload.refresh_token)
    return {"ok": True}


@router.get("/me", response_model=UserProfile)
async def me(user: User = Depends(get_current_user)) -> UserProfile:
    return _to_profile(user)
