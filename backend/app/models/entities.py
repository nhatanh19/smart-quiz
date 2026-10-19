import enum
from datetime import datetime
from typing import List, Optional, Any
from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
    JSON,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

# Postgres JSONB with fallback to standard JSON for maximum compatibility
JSONBType = JSON().with_variant(JSONB, "postgresql")


# ==============================================================================
# ENUM DEFINITIONS (Section 3.1)
# ==============================================================================


class UserRole(str, enum.Enum):
    """User roles for Role-Based Access Control (RBAC)."""
    ADMIN = "ADMIN"
    INSTRUCTOR = "INSTRUCTOR"
    STUDENT = "STUDENT"


class QuestionType(str, enum.Enum):
    """Supported question formats."""
    SINGLE_CHOICE = "SINGLE_CHOICE"
    MULTIPLE_CHOICE = "MULTIPLE_CHOICE"
    TRUE_FALSE = "TRUE_FALSE"


class CognitiveLevel(str, enum.Enum):
    """Bloom's revised taxonomy cognitive levels."""
    REMEMBER = "REMEMBER"      # Nhận biết
    UNDERSTAND = "UNDERSTAND"  # Thông hiểu
    APPLY = "APPLY"            # Vận dụng


class AttemptStatus(str, enum.Enum):
    """Lifecycle status of a student's exam attempt."""
    IN_PROGRESS = "IN_PROGRESS"
    SUBMITTED = "SUBMITTED"
    LOCKED_VIOLATION = "LOCKED_VIOLATION"
    EXPIRED = "EXPIRED"


class QuestionSourceType(str, enum.Enum):
    """Origin of the question in the question bank."""
    MANUAL = "MANUAL"
    FILE_PARSER = "FILE_PARSER"
    AI_GENERATED = "AI_GENERATED"


class AntiCheatEventType(str, enum.Enum):
    """Browser anti-cheat violation event types."""
    TAB_SWITCH = "TAB_SWITCH"
    WINDOW_BLUR = "WINDOW_BLUR"
    COPY_PASTE_ATTEMPT = "COPY_PASTE_ATTEMPT"


# ==============================================================================
# TABLE ENTITIES (Section 3.1)
# ==============================================================================


class User(Base):
    """User entity: Administrator, Instructor, or Student."""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, native_enum=False, length=20),
        nullable=False,
        default=UserRole.STUDENT,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    created_categories: Mapped[List["Category"]] = relationship(
        "Category", back_populates="creator", cascade="all, delete-orphan"
    )
    created_questions: Mapped[List["Question"]] = relationship(
        "Question", back_populates="creator", cascade="all, delete-orphan"
    )
    instructed_exams: Mapped[List["Exam"]] = relationship(
        "Exam", back_populates="instructor", cascade="all, delete-orphan"
    )
    exam_attempts: Mapped[List["ExamAttempt"]] = relationship(
        "ExamAttempt", back_populates="student", cascade="all, delete-orphan"
    )


class Category(Base):
    """Topic or Course Subject grouping questions."""
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    creator: Mapped["User"] = relationship("User", back_populates="created_categories")
    questions: Mapped[List["Question"]] = relationship(
        "Question", back_populates="category", cascade="all, delete-orphan"
    )


class Question(Base):
    """Question Bank entity with options stored as JSONB."""
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    category_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True
    )
    creator_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[QuestionType] = mapped_column(
        Enum(QuestionType, native_enum=False, length=30), nullable=False
    )
    cognitive_level: Mapped[CognitiveLevel] = mapped_column(
        Enum(CognitiveLevel, native_enum=False, length=30), nullable=False
    )
    # Options stored as JSONB array: [{"id": "A", "text": "...", "is_correct": true}]
    options: Mapped[Any] = mapped_column(JSONBType, nullable=False)
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_type: Mapped[QuestionSourceType] = mapped_column(
        Enum(QuestionSourceType, native_enum=False, length=30),
        default=QuestionSourceType.MANUAL,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    category: Mapped[Optional["Category"]] = relationship("Category", back_populates="questions")
    creator: Mapped["User"] = relationship("User", back_populates="created_questions")
    exam_associations: Mapped[List["ExamQuestion"]] = relationship(
        "ExamQuestion", back_populates="question", cascade="all, delete-orphan"
    )
    attempt_answers: Mapped[List["AttemptAnswer"]] = relationship(
        "AttemptAnswer", back_populates="question", cascade="all, delete-orphan"
    )


class Exam(Base):
    """Exam definition configured by an instructor."""
    __tablename__ = "exams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    instructor_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    duration_minutes: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    start_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    access_password: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    max_attempts: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    max_tab_violations: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    shuffle_questions: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    shuffle_options: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # JSONB storing matrix configuration (e.g. ratio of REMEMBER, UNDERSTAND, APPLY)
    matrix_config: Mapped[Optional[Any]] = mapped_column(JSONBType, nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    instructor: Mapped["User"] = relationship("User", back_populates="instructed_exams")
    exam_questions: Mapped[List["ExamQuestion"]] = relationship(
        "ExamQuestion", back_populates="exam", cascade="all, delete-orphan", order_by="ExamQuestion.order_index"
    )
    attempts: Mapped[List["ExamAttempt"]] = relationship(
        "ExamAttempt", back_populates="exam", cascade="all, delete-orphan"
    )


class ExamQuestion(Base):
    """Association table linking exams and questions with order and points."""
    __tablename__ = "exam_questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    exam_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("exams.id", ondelete="CASCADE"), nullable=False, index=True
    )
    question_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    points: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)

    # Relationships
    exam: Mapped["Exam"] = relationship("Exam", back_populates="exam_questions")
    question: Mapped["Question"] = relationship("Question", back_populates="exam_associations")


class ExamAttempt(Base):
    """Student exam submission / session attempt."""
    __tablename__ = "exam_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    exam_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("exams.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    status: Mapped[AttemptStatus] = mapped_column(
        Enum(AttemptStatus, native_enum=False, length=30),
        default=AttemptStatus.IN_PROGRESS,
        nullable=False,
    )
    violation_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # JSONB snapshot preserving shuffled question & option order specifically for this student
    question_order_snapshot: Mapped[Optional[Any]] = mapped_column(JSONBType, nullable=True)

    # Relationships
    exam: Mapped["Exam"] = relationship("Exam", back_populates="attempts")
    student: Mapped["User"] = relationship("User", back_populates="exam_attempts")
    answers: Mapped[List["AttemptAnswer"]] = relationship(
        "AttemptAnswer", back_populates="attempt", cascade="all, delete-orphan"
    )
    anti_cheat_logs: Mapped[List["AntiCheatLog"]] = relationship(
        "AntiCheatLog", back_populates="attempt", cascade="all, delete-orphan"
    )


class AttemptAnswer(Base):
    """Individual answer record for each question in an exam attempt."""
    __tablename__ = "attempt_answers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    attempt_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("exam_attempts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    question_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # JSONB storing array of chosen option IDs (e.g. ["A", "C"])
    selected_options: Mapped[Optional[Any]] = mapped_column(JSONBType, nullable=True)
    is_correct: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    # JSONB storing contextual explanations and recommendation from AI Tutor
    ai_tutor_feedback: Mapped[Optional[Any]] = mapped_column(JSONBType, nullable=True)

    # Relationships
    attempt: Mapped["ExamAttempt"] = relationship("ExamAttempt", back_populates="answers")
    question: Mapped["Question"] = relationship("Question", back_populates="attempt_answers")


class AntiCheatLog(Base):
    """Audit log tracking client-side security events and violations."""
    __tablename__ = "anti_cheat_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    attempt_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("exam_attempts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # String event type: TAB_SWITCH, WINDOW_BLUR, COPY_PASTE_ATTEMPT
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    logged_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    # JSONB storing contextual browser metadata (timestamp, window dimensions, details)
    metadata_info: Mapped[Optional[Any]] = mapped_column(JSONBType, nullable=True)

    # Relationships
    attempt: Mapped["ExamAttempt"] = relationship("ExamAttempt", back_populates="anti_cheat_logs")
