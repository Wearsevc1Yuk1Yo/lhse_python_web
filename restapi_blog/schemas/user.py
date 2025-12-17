from typing import Optional

from pydantic import BaseModel, validator


class UserCreate(BaseModel):
    email: str
    login: str
    password: str

    @validator("email")
    def email_valid(cls, v):
        if "@" not in v or "." not in v:
            raise ValueError("Некорректный формат email")
        return v

    @validator("login")
    def login_length(cls, v):
        if len(v) < 2:
            raise ValueError("Логин должен содержать минимум 2 символа")
        return v

    @validator("password")
    def password_length(cls, v):
        if len(v) < 3:
            raise ValueError("Пароль должен содержать минимум 3 символа")
        return v


class UserUpdate(BaseModel):
    email: Optional[str] = None
    login: Optional[str] = None
    password: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    email: str
    login: str
    created_at: str
    updated_at: str
