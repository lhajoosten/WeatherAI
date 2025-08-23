from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


# User Schemas
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=100)
    timezone: str = Field(default="UTC", max_length=50)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    timezone: str
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# Location Schemas
class LocationCreate(BaseModel):
    name: str = Field(max_length=255)
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    timezone: str | None = Field(default=None, max_length=50)


class LocationResponse(BaseModel):
    id: int
    name: str
    lat: float
    lon: float
    timezone: str | None
    created_at: datetime

    class Config:
        from_attributes = True


# Explain Schemas
class ExplainResponse(BaseModel):
    summary: str
    actions: list[str]
    driver: str
    tokens_in: int
    tokens_out: int
    model: str


# Health Schema
class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: datetime
    services: dict


# Error Schemas
class ErrorDetail(BaseModel):
    type: str
    title: str
    detail: str
    status: int


class ValidationErrorDetail(BaseModel):
    loc: list[str]
    msg: str
    type: str


class ValidationErrorResponse(BaseModel):
    type: str = "validation_error"
    title: str = "Validation Error"
    detail: str
    status: int = 422
    errors: list[ValidationErrorDetail]
