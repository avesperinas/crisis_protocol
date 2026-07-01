"""Password hashing, JWT issuance/verification, and refresh-token session management.

Access tokens are stateless JWTs (short-lived, 15 min default). Refresh tokens are
opaque random strings, stored hashed in `user_sessions`, and rotated on every use —
so a leaked refresh token can be invalidated by revoking its session row.
"""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.models import User, UserSession


class AuthServiceError(ValueError):
    pass


class InvalidCredentialsError(AuthServiceError):
    pass


class EmailTakenError(AuthServiceError):
    pass


class UsernameTakenError(AuthServiceError):
    pass


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _as_aware_utc(dt: datetime) -> datetime:
    """SQLite drops tzinfo on round-trip even for DateTime(timezone=True) columns."""
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=UTC)


def create_access_token(user_id: str) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": user_id,
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_access_token_minutes),
        "type": "access",
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> str:
    """Returns the user_id encoded in a valid access token. Raises jwt.PyJWTError on failure."""
    payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    if payload.get("type") != "access":
        raise jwt.InvalidTokenError("not an access token")
    return payload["sub"]


async def register_user(
    session: AsyncSession, *, email: str, username: str, password: str, locale: str = "es"
) -> User:
    email = email.strip().lower()
    username = username.strip()

    existing_email = (
        await session.execute(select(User).where(User.email == email))
    ).scalar_one_or_none()
    if existing_email:
        raise EmailTakenError("email already registered")

    existing_username = (
        await session.execute(select(User).where(User.username == username))
    ).scalar_one_or_none()
    if existing_username:
        raise UsernameTakenError("username already taken")

    user = User(
        email=email,
        username=username,
        password_hash=hash_password(password),
        locale=locale,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def authenticate_user(session: AsyncSession, *, email: str, password: str) -> User:
    email = email.strip().lower()
    user = (
        await session.execute(select(User).where(User.email == email))
    ).scalar_one_or_none()
    if not user or not verify_password(password, user.password_hash):
        raise InvalidCredentialsError("invalid email or password")
    return user


async def create_session(session: AsyncSession, *, user_id: str) -> str:
    """Creates a refresh-token session and returns the raw (unhashed) token."""
    raw_token = secrets.token_urlsafe(48)
    expires_at = datetime.now(UTC) + timedelta(days=settings.jwt_refresh_token_days)
    session.add(
        UserSession(
            user_id=user_id,
            refresh_token_hash=_hash_token(raw_token),
            expires_at=expires_at,
        )
    )
    await session.commit()
    return raw_token


async def rotate_session(session: AsyncSession, *, refresh_token: str) -> tuple[User, str]:
    """Validates + revokes a refresh token, issues a new one. Returns (user, new_raw_token)."""
    token_hash = _hash_token(refresh_token)
    user_session = (
        await session.execute(
            select(UserSession).where(UserSession.refresh_token_hash == token_hash)
        )
    ).scalar_one_or_none()
    if not user_session or _as_aware_utc(user_session.expires_at) < datetime.now(UTC):
        raise InvalidCredentialsError("invalid or expired refresh token")

    user = (
        await session.execute(select(User).where(User.id == user_session.user_id))
    ).scalar_one_or_none()
    if not user:
        raise InvalidCredentialsError("user not found")

    await session.delete(user_session)
    await session.commit()
    new_raw_token = await create_session(session, user_id=user.id)
    return user, new_raw_token


async def revoke_session(session: AsyncSession, *, refresh_token: str) -> None:
    token_hash = _hash_token(refresh_token)
    user_session = (
        await session.execute(
            select(UserSession).where(UserSession.refresh_token_hash == token_hash)
        )
    ).scalar_one_or_none()
    if user_session:
        await session.delete(user_session)
        await session.commit()


async def get_user_by_id(session: AsyncSession, user_id: str) -> User | None:
    return (await session.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
