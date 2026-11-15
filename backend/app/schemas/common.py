from datetime import datetime
from typing import Generic, Optional, TypeVar, Any, List
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator
from app.models.entities import (
    AttemptStatus,
    CognitiveLevel,
    QuestionLevel,
    QuestionType,
    QuestionSource,
    UserRole,
)

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


class SubjectCreateSchema(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=2000)

    @field_validator("name", "description", mode="before")
    @classmethod
    def strip_subject_text(cls, value: Any) -> Any:
        return value.strip() if isinstance(value, str) else value


class SubjectResponseSchema(SubjectCreateSchema):
    id: uuid.UUID
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CategoryCreateSchema(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=2000)
    subject_id: uuid.UUID

    @field_validator("name", "description", mode="before")
    @classmethod
    def strip_category_text(cls, value: Any) -> Any:
        return value.strip() if isinstance(value, str) else value


class CategoryUpdateSchema(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=2000)
    subject_id: Optional[uuid.UUID] = None

    @field_validator("name", "description", mode="before")
    @classmethod
    def strip_category_text(cls, value: Any) -> Any:
        return value.strip() if isinstance(value, str) else value

    @model_validator(mode="after")
    def require_update_fields(self) -> "CategoryUpdateSchema":
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided")
        return self


class CategoryResponseSchema(BaseModel):
    name: str
    description: Optional[str] = None
    subject_id: Optional[uuid.UUID] = None
    id: uuid.UUID
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QuestionOptionSchema(BaseModel):
    """Option structure stored inside Question.options JSONB."""
    id: str = Field(min_length=1, max_length=32)  # e.g. "A", "B", "C", "D"
    text: str = Field(min_length=1)
    is_correct: bool = False

    @field_validator("id", "text", mode="before")
    @classmethod
    def strip_option_text(cls, value: Any) -> Any:
        return value.strip() if isinstance(value, str) else value


class QuestionBaseSchema(BaseModel):
    """Standard schema for question definition."""
    category_id: uuid.UUID
    content: str = Field(min_length=1)
    question_type: QuestionType
    cognitive_level: CognitiveLevel
    level: QuestionLevel = QuestionLevel.MEDIUM
    options: List[QuestionOptionSchema] = Field(min_length=2, max_length=10)
    tags: List[str] = Field(default_factory=list, max_length=20)
    explanation: Optional[str] = Field(default=None, min_length=1)

    @field_validator("content", "explanation", mode="before")
    @classmethod
    def strip_question_text(cls, value: Any) -> Any:
        return value.strip() if isinstance(value, str) else value

    @field_validator("tags", mode="before")
    @classmethod
    def normalize_tags(cls, value: Any) -> Any:
        if not isinstance(value, list):
            return value
        normalized = []
        seen = set()
        for tag in value:
            if not isinstance(tag, str):
                normalized.append(tag)
                continue
            tag = tag.strip()
            if tag and tag.casefold() not in seen:
                normalized.append(tag)
                seen.add(tag.casefold())
        return normalized

    @field_validator("tags")
    @classmethod
    def validate_tag_lengths(cls, value: List[str]) -> List[str]:
        if any(len(tag) > 40 for tag in value):
            raise ValueError("Tags must be 40 characters or fewer")
        return value

    @model_validator(mode="after")
    def validate_options(self) -> "QuestionBaseSchema":
        option_ids = [option.id for option in self.options]
        if len(option_ids) != len(set(option_ids)):
            raise ValueError("Option IDs must be unique")

        correct_count = sum(option.is_correct for option in self.options)
        if self.question_type in (QuestionType.SINGLE_CHOICE, QuestionType.TRUE_FALSE):
            if correct_count != 1:
                raise ValueError("This question type must have exactly one correct option")
        elif correct_count < 1:
            raise ValueError("A multiple-choice question must have at least one correct option")

        if self.question_type == QuestionType.TRUE_FALSE and len(self.options) != 2:
            raise ValueError("A true/false question must have exactly two options")
        return self


class QuestionCreateSchema(QuestionBaseSchema):
    """Payload for creating a question in the bank."""
    source_type: QuestionSource = QuestionSource.MANUAL


class QuestionUpdateSchema(BaseModel):
    """Payload for partially updating a question in the bank."""
    category_id: Optional[uuid.UUID] = None
    content: Optional[str] = Field(default=None, min_length=1)
    question_type: Optional[QuestionType] = None
    cognitive_level: Optional[CognitiveLevel] = None
    level: Optional[QuestionLevel] = None
    options: Optional[List[QuestionOptionSchema]] = Field(
        default=None, min_length=2, max_length=10
    )
    tags: Optional[List[str]] = Field(default=None, max_length=20)
    explanation: Optional[str] = Field(default=None, min_length=1)

    @field_validator("content", "explanation", mode="before")
    @classmethod
    def strip_question_text(cls, value: Any) -> Any:
        return value.strip() if isinstance(value, str) else value

    @field_validator("tags", mode="before")
    @classmethod
    def normalize_tags(cls, value: Any) -> Any:
        if not isinstance(value, list):
            return value
        normalized = []
        seen = set()
        for tag in value:
            if not isinstance(tag, str):
                normalized.append(tag)
                continue
            tag = tag.strip()
            if tag and tag.casefold() not in seen:
                normalized.append(tag)
                seen.add(tag.casefold())
        return normalized

    @field_validator("tags")
    @classmethod
    def validate_tag_lengths(cls, value: Optional[List[str]]) -> Optional[List[str]]:
        if value is not None and any(len(tag) > 40 for tag in value):
            raise ValueError("Tags must be 40 characters or fewer")
        return value

    @model_validator(mode="after")
    def require_update_fields(self) -> "QuestionUpdateSchema":
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided")
        return self


class QuestionResponseSchema(QuestionBaseSchema):
    """Question returned by the bank API."""
    id: uuid.UUID
    creator_id: uuid.UUID
    source_type: QuestionSource
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
