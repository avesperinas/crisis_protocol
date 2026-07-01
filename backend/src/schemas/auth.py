"""Pydantic models for the auth REST API."""

import re

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

_USERNAME_RE = re.compile(r"^[a-zA-Z0-9_]+$")


class UserRegister(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    username: str = Field(min_length=3, max_length=24)
    password: str = Field(min_length=8, max_length=128)
    locale: str = "es"

    @field_validator("username")
    @classmethod
    def _username_charset(cls, v: str) -> str:
        if not _USERNAME_RE.match(v):
            raise ValueError("username may only contain letters, numbers, and underscores")
        return v


class UserLogin(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    refresh_token: str


class UserProfile(BaseModel):
    id: str
    email: str
    username: str
    locale: str
    created_at: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserProfile
