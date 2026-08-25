from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
    plan: str
    is_admin: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AdminUpdateUserRequest(BaseModel):
    plan: str | None = None
    is_admin: bool | None = None


class AdminUserResponse(UserResponse):
    search_count: int


class AdminStatsResponse(BaseModel):
    total_users: int
    pro_users: int
    admin_users: int
    total_searches: int
    searches_via_llm: int
    searches_via_rule_based: int
    catalog_size: int


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)


class UpdateProfileRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    message: str
    # Dev-mode only: no email provider is configured, so the reset token is
    # returned directly instead of being emailed. Remove this field once
    # real email delivery (SMTP/SendGrid/etc.) is wired up.
    dev_reset_token: str | None = None


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)


class PlanCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, pattern=r"^[a-z0-9_-]+$")
    display_name: str = Field(..., min_length=1, max_length=100)
    price_label: str = Field(..., min_length=1, max_length=50)
    period: str | None = Field(default=None, max_length=50)
    description: str = Field(..., min_length=1, max_length=500)
    features: list[str] = Field(default_factory=list)
    daily_search_limit: int | None = Field(default=None, ge=1)


class PlanUpdateRequest(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=100)
    price_label: str | None = Field(default=None, min_length=1, max_length=50)
    period: str | None = None
    description: str | None = Field(default=None, min_length=1, max_length=500)
    features: list[str] | None = None
    daily_search_limit: int | None = Field(default=None, ge=1)
    # No plain daily_search_limit=None here on purpose — PATCH can't tell
    # "leave it alone" apart from "set it to unlimited". Use the dedicated
    # flag instead.
    clear_search_limit: bool = False


class PlanResponse(BaseModel):
    id: str
    name: str
    display_name: str
    price_label: str
    period: str | None
    description: str
    features: list[str]
    daily_search_limit: int | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UsageResponse(BaseModel):
    plan: str
    limit: int | None
    used: int
    remaining: int | None
