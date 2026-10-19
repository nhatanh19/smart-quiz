from datetime import datetime
from typing import Generic, Optional, TypeVar, Any, List
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from app.models.entities import UserRole, QuestionType, CognitiveLevel, AttemptStatus

import uuid

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Standard API response wrapper."""
    success: bool = True
    message: str = "Operation successful"
    data: Optional[T] = None


class ErrorResponse(BaseModel):
    """Standard error response structure."""
    success: bool = False
    error: str
    details: Optional[Any] = None


class HealthCheckResponse(BaseModel):
    """Health check endpoint response."""
    status: str = "healthy"
    service: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class TokenPayload(BaseModel):
    """Decoded JWT payload."""
    sub: str  # User ID or Email
    role: UserRole
    exp: Optional[int] = None


class TokenResponse(BaseModel):
    """Login authentication response."""
    access_token: str
    token_type: str = "bearer"
    role: UserRole
    full_name: str
    user_id: uuid.UUID


class UserBase(BaseModel):
    """Common user attributes."""
    email: EmailStr
    full_name: str
    role: UserRole = UserRole.STUDENT


class UserCreate(UserBase):
    """Schema for registering a new user."""
    password: str = Field(min_length=6)


class UserResponse(UserBase):
    """Public user response schema."""
    id: uuid.UUID
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QuestionOptionSchema(BaseModel):
    """Option structure stored inside Question.options JSONB."""
    id: str  # e.g. "A", "B", "C", "D"
    text: str
    is_correct: bool = False


class QuestionBaseSchema(BaseModel):
    """Standard schema for question definition."""
    content: str
    question_type: QuestionType
    cognitive_level: CognitiveLevel
    options: List[QuestionOptionSchema]
    explanation: Optional[str] = None
