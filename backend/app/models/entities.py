import enum
import uuid
from datetime import datetime
from typing import Any, List, Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    desc,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


# ==============================================================================
# 3.1 KIỂU ENUM (Khớp 100% mục 3.1)
# ==============================================================================


class UserRole(str, enum.Enum):
    """User roles enum in PostgreSQL: user_role."""
    ADMIN = "ADMIN"
    INSTRUCTOR = "INSTRUCTOR"
    STUDENT = "STUDENT"


class QuestionType(str, enum.Enum):
    """Question formats enum in PostgreSQL: question_type."""
    SINGLE_CHOICE = "SINGLE_CHOICE"
    MULTIPLE_CHOICE = "MULTIPLE_CHOICE"
    TRUE_FALSE = "TRUE_FALSE"


class CognitiveLevel(str, enum.Enum):
    """Bloom taxonomy levels enum in PostgreSQL: cognitive_level."""
    REMEMBER = "REMEMBER"
    UNDERSTAND = "UNDERSTAND"
    APPLY = "APPLY"


class QuestionLevel(str, enum.Enum):
    """Question difficulty levels enum in PostgreSQL: question_level."""
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"


class AttemptStatus(str, enum.Enum):
    """Exam attempt lifecycle enum in PostgreSQL: attempt_status."""
    IN_PROGRESS = "IN_PROGRESS"
    SUBMITTED = "SUBMITTED"
    LOCKED_VIOLATION = "LOCKED_VIOLATION"
    EXPIRED = "EXPIRED"


class QuestionSource(str, enum.Enum):
    """Question origin enum in PostgreSQL: question_source."""
    MANUAL = "MANUAL"
    FILE_PARSER = "FILE_PARSER"
    AI_GENERATED = "AI_GENERATED"


# Alias for backward compatibility
QuestionSourceType = QuestionSource


# ==============================================================================
# 3.2 BẢNG THỰC THỂ (PostgreSQL DDL Models)
# ==============================================================================


# 1) users
class User(Base):
    """User account entity."""
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, name="user_role", native_enum=True),
        nullable=False,
        server_default="STUDENT",
        default=UserRole.STUDENT,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("true"),
        default=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        UniqueConstraint("email", name="email"),
        CheckConstraint("email = lower(email)", name="email_lowercase"),
    )

    # Relationships
    created_categories: Mapped[List["Category"]] = relationship(
        "Category", back_populates="creator", passive_deletes="all"
    )
    created_subjects: Mapped[List["Subject"]] = relationship(
        "Subject", back_populates="creator", passive_deletes="all"
    )
    created_questions: Mapped[List["Question"]] = relationship(
        "Question", back_populates="creator", passive_deletes="all"
    )
    instructed_exams: Mapped[List["Exam"]] = relationship(
        "Exam", back_populates="instructor", passive_deletes="all"
    )
    exam_attempts: Mapped[List["ExamAttempt"]] = relationship(
        "ExamAttempt", back_populates="student", passive_deletes="all"
    )


# 2) subjects (môn học)
class Subject(Base):
    """Subject containing question-bank topics."""
    __tablename__ = "subjects"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        UniqueConstraint("created_by", "name", name="created_by_name"),
        Index("ix_subjects_created_by", "created_by"),
    )

    creator: Mapped["User"] = relationship("User", back_populates="created_subjects")
    categories: Mapped[List["Category"]] = relationship(
        "Category", back_populates="subject", passive_deletes="all"
    )


# 3) categories (chuyên đề)
class Category(Base):
    """Category/Topic entity."""
    __tablename__ = "categories"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    subject_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("subjects.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        UniqueConstraint(
            "created_by",
            "subject_id",
            "name",
            name="created_by_subject_name",
        ),
        Index("ix_categories_subject_id", "subject_id"),
    )

    # Relationships
    creator: Mapped["User"] = relationship("User", back_populates="created_categories")
    subject: Mapped[Optional["Subject"]] = relationship(
        "Subject", back_populates="categories"
    )
    questions: Mapped[List["Question"]] = relationship(
        "Question", back_populates="category", passive_deletes="all"
    )


# 3) questions (ngân hàng câu hỏi)
class Question(Base):
    """Question Bank entity."""
    __tablename__ = "questions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False,
    )
    creator_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[QuestionType] = mapped_column(
        SAEnum(QuestionType, name="question_type", native_enum=True),
        nullable=False,
    )
    cognitive_level: Mapped[CognitiveLevel] = mapped_column(
        SAEnum(CognitiveLevel, name="cognitive_level", native_enum=True),
        nullable=False,
    )
    level: Mapped[QuestionLevel] = mapped_column(
        SAEnum(QuestionLevel, name="question_level", native_enum=True),
        nullable=False,
        server_default="MEDIUM",
        default=QuestionLevel.MEDIUM,
    )
    options: Mapped[Any] = mapped_column(JSONB, nullable=False)
    tags: Mapped[List[str]] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'[]'::jsonb"),
        default=list,
    )
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_type: Mapped[QuestionSource] = mapped_column(
        SAEnum(QuestionSource, name="question_source", native_enum=True),
        nullable=False,
        server_default="MANUAL",
        default=QuestionSource.MANUAL,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        CheckConstraint(
            "CASE WHEN jsonb_typeof(options) = 'array' "
            "THEN jsonb_array_length(options) BETWEEN 2 AND 10 "
            "ELSE false END",
            name="options_is_array",
        ),
        CheckConstraint(
            "jsonb_typeof(tags) = 'array'",
            name="tags_is_array",
        ),
        Index("ix_questions_creator_category", "creator_id", "category_id"),
        Index("ix_questions_matrix", "category_id", "cognitive_level", "question_type"),
        Index("ix_questions_category_level", "category_id", "level"),
        Index(
            "ix_questions_content_trgm",
            "content",
            postgresql_using="gin",
            postgresql_ops={"content": "gin_trgm_ops"},
        ),
        Index("ix_questions_tags", "tags", postgresql_using="gin"),
    )

    # Relationships
    category: Mapped["Category"] = relationship("Category", back_populates="questions")
    creator: Mapped["User"] = relationship("User", back_populates="created_questions")
    exam_questions: Mapped[List["ExamQuestion"]] = relationship(
        "ExamQuestion", back_populates="question", passive_deletes="all"
    )
    attempt_answers: Mapped[List["AttemptAnswer"]] = relationship(
        "AttemptAnswer", back_populates="question", passive_deletes="all"
    )


# 4) exams (kỳ thi / đề thi)
class Exam(Base):
    """Exam definition."""
    __tablename__ = "exams"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    exam_code: Mapped[str] = mapped_column(String(12), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    instructor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    start_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    access_password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    max_attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="1",
        default=1,
    )
    max_tab_violations: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="3",
        default=3,
    )
    shuffle_questions: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("true"),
        default=True,
    )
    shuffle_options: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("true"),
        default=True,
    )
    matrix_config: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)
    is_published: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("false"),
        default=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        UniqueConstraint("exam_code", name="exam_code"),
        CheckConstraint("duration_minutes > 0", name="duration_positive"),
        CheckConstraint("max_attempts >= 1", name="max_attempts_min"),
        CheckConstraint("max_tab_violations >= 1", name="max_tab_violations_min"),
        CheckConstraint(
            "start_time IS NULL OR end_time IS NULL OR end_time > start_time",
            name="time_window",
        ),
        CheckConstraint(
            "NOT is_published OR (start_time IS NOT NULL AND end_time IS NOT NULL)",
            name="published_has_window",
        ),
        CheckConstraint(
            "matrix_config IS NULL OR jsonb_typeof(matrix_config) = 'object'",
            name="matrix_config_object",
        ),
        Index("ix_exams_instructor_id", "instructor_id"),
        Index("ix_exams_published_start", "is_published", "start_time"),
    )

    # Relationships
    instructor: Mapped["User"] = relationship("User", back_populates="instructed_exams")
    exam_questions: Mapped[List["ExamQuestion"]] = relationship(
        "ExamQuestion", back_populates="exam", cascade="all, delete-orphan", passive_deletes=True
    )
    attempts: Mapped[List["ExamAttempt"]] = relationship(
        "ExamAttempt", back_populates="exam", passive_deletes="all"
    )


# 5) exam_questions (đề thi - câu hỏi)
class ExamQuestion(Base):
    """Exam-Question association table."""
    __tablename__ = "exam_questions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    exam_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("exams.id", ondelete="CASCADE"),
        nullable=False,
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("questions.id", ondelete="RESTRICT"),
        nullable=False,
    )
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    points: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        server_default="1.0",
        default=1.0,
    )

    __table_args__ = (
        UniqueConstraint("exam_id", "question_id", name="exam_question"),
        UniqueConstraint(
            "exam_id",
            "order_index",
            name="exam_order",
            deferrable=True,
            initially="DEFERRED",
        ),
        CheckConstraint("order_index >= 1", name="order_index_min"),
        CheckConstraint("points > 0", name="points_positive"),
        Index("ix_exam_questions_question_id", "question_id"),
    )

    # Relationships
    exam: Mapped["Exam"] = relationship("Exam", back_populates="exam_questions")
    question: Mapped["Question"] = relationship("Question", back_populates="exam_questions")


# 6) exam_attempts (lượt làm bài)
class ExamAttempt(Base):
    """Exam attempt / session."""
    __tablename__ = "exam_attempts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    exam_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("exams.id", ondelete="RESTRICT"),
        nullable=False,
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    attempt_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="1",
        default=1,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    submitted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    status: Mapped[AttemptStatus] = mapped_column(
        SAEnum(AttemptStatus, name="attempt_status", native_enum=True),
        nullable=False,
        server_default="IN_PROGRESS",
        default=AttemptStatus.IN_PROGRESS,
    )
    violation_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="0",
        default=0,
    )
    question_order_snapshot: Mapped[Any] = mapped_column(JSONB, nullable=False)

    __table_args__ = (
        UniqueConstraint("exam_id", "student_id", "attempt_number", name="exam_student_no"),
        CheckConstraint("attempt_number >= 1", name="attempt_number_min"),
        CheckConstraint(
            "score IS NULL OR (score >= 0 AND score <= 10)",
            name="score_range",
        ),
        CheckConstraint("violation_count >= 0", name="violation_count_min"),
        CheckConstraint(
            "(status = 'IN_PROGRESS' AND submitted_at IS NULL) OR "
            "(status <> 'IN_PROGRESS' AND submitted_at IS NOT NULL)",
            name="closed_at_matches_status",
        ),
        CheckConstraint(
            "jsonb_typeof(question_order_snapshot) = 'object'",
            name="snapshot_object",
        ),
        Index(
            "uq_exam_attempts_one_in_progress",
            "exam_id",
            "student_id",
            unique=True,
            postgresql_where=text("status = 'IN_PROGRESS'"),
            sqlite_where=text("status = 'IN_PROGRESS'"),
        ),
        Index("ix_exam_attempts_student_started", "student_id", desc("started_at")),
        Index(
            "ix_exam_attempts_open_expires",
            "expires_at",
            postgresql_where=text("status = 'IN_PROGRESS'"),
        ),
    )

    # Relationships
    exam: Mapped["Exam"] = relationship("Exam", back_populates="attempts")
    student: Mapped["User"] = relationship("User", back_populates="exam_attempts")
    answers: Mapped[List["AttemptAnswer"]] = relationship(
        "AttemptAnswer", back_populates="attempt", cascade="all, delete-orphan", passive_deletes=True
    )
    anti_cheat_logs: Mapped[List["AntiCheatLog"]] = relationship(
        "AntiCheatLog", back_populates="attempt", cascade="all, delete-orphan", passive_deletes=True
    )


# 7) attempt_answers (chi tiết câu trả lời)
class AttemptAnswer(Base):
    """Attempt answer record."""
    __tablename__ = "attempt_answers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    attempt_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("exam_attempts.id", ondelete="CASCADE"),
        nullable=False,
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("questions.id", ondelete="RESTRICT"),
        nullable=False,
    )
    selected_options: Mapped[Any] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'[]'::jsonb"),
    )
    is_correct: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    points_awarded: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ai_tutor_feedback: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        UniqueConstraint("attempt_id", "question_id", name="attempt_question"),
        CheckConstraint("jsonb_typeof(selected_options) = 'array'", name="selected_options_is_array"),
        CheckConstraint("points_awarded IS NULL OR points_awarded >= 0", name="points_awarded_min"),
        CheckConstraint(
            "ai_tutor_feedback IS NULL OR jsonb_typeof(ai_tutor_feedback) = 'object'",
            name="feedback_object",
        ),
        Index("ix_attempt_answers_question_id", "question_id"),
    )

    # Relationships
    attempt: Mapped["ExamAttempt"] = relationship("ExamAttempt", back_populates="answers")
    question: Mapped["Question"] = relationship("Question", back_populates="attempt_answers")


# 8) anti_cheat_logs (nhật ký chống gian lận)
class AntiCheatLog(Base):
    """Anti-cheat audit log."""
    __tablename__ = "anti_cheat_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    attempt_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("exam_attempts.id", ondelete="CASCADE"),
        nullable=False,
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    logged_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    metadata_info: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "metadata_info IS NULL OR jsonb_typeof(metadata_info) = 'object'",
            name="metadata_object",
        ),
        Index("ix_anti_cheat_logs_attempt_logged", "attempt_id", "logged_at"),
    )

    # Relationships
    attempt: Mapped["ExamAttempt"] = relationship("ExamAttempt", back_populates="anti_cheat_logs")
