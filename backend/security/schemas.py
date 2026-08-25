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
