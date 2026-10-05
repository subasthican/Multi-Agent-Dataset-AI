from datetime import datetime, timezone

from pydantic import BaseModel, EmailStr, Field, field_validator


class PasswordInput(BaseModel):
    @field_validator("password", "new_password", check_fields=False)
    @classmethod
    def bcrypt_length(cls, value):
        if len(value.encode()) > 72:
            raise ValueError("Password must be at most 72 UTF-8 bytes")
        return value


class RegisterRequest(PasswordInput):
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
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AdminUpdateUserRequest(BaseModel):
    plan: str | None = None
    is_admin: bool | None = None
    is_active: bool | None = None


class AdminUserResponse(UserResponse):
    search_count: int


class AdminSearchHistoryItem(BaseModel):
    id: str
    query: str
    domain: str
    task: str
    understanding_source: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AdminUserDetailResponse(AdminUserResponse):
    search_history: list[AdminSearchHistoryItem]


class AdminStatsResponse(BaseModel):
    total_users: int
    pro_users: int
    admin_users: int
    total_searches: int
    searches_via_llm: int
    searches_via_rule_based: int
    catalog_size: int


class ChangePasswordRequest(PasswordInput):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)


class UpdateProfileRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    message: str



class ResetPasswordRequest(PasswordInput):
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


class AdminDeleteRequest(PasswordInput):
    password: str = Field(..., min_length=1, max_length=72, repr=False)


class AdminAuditResponse(BaseModel):
    id: str
    actor_id: str
    action: str
    target_type: str
    target_id: str
    changed_fields: list[str]
    created_at: datetime
    model_config = {"from_attributes": True}

    @field_validator("created_at")
    @classmethod
    def utc_timestamp(cls, value):
        return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value
