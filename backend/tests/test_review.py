"""Tests for Post-Exam Review Mode Interface (Issue #15, WBS 5.1.2).

Validates:
- Endpoint GET /api/v1/tutor-analytics/review/{attempt_id}
- Service get_exam_review_data
- RBAC permissions (Student own attempt vs other student vs Instructor)
- Review state validation (cannot review IN_PROGRESS attempts)
- Detailed question review items: correct/incorrect status, options alignment, standard answer keys
- Question and option order preservation from question_order_snapshot
- Score and time spent metrics
"""

from datetime import datetime, timedelta, timezone
import json
import uuid

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine, event, TextClause, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.database import get_db
from app.core.security import create_access_token
from app.main import app
from app.models.entities import (
    AttemptAnswer,
    AttemptStatus,
    Base,
    Category,
    CognitiveLevel,
    Exam,
    ExamAttempt,
    ExamQuestion,
    Question,
    QuestionType,
    User,
    UserRole,
)
from app.modules.tutor_analytics.exceptions import (
    InvalidAttemptStateError,
    NotFoundError,
)
from app.modules.tutor_analytics.services.review_service import get_exam_review_data


@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(type_, compiler, **kw):
    return "JSON"


@compiles(UniqueConstraint, "sqlite")
def compile_unique_sqlite(element, compiler, **kw):
    cols = ", ".join(
        compiler.preparer.quote(c.name) if hasattr(c, "name") else str(c)
        for c in element.columns
    )
    name = f"CONSTRAINT {compiler.preparer.quote(element.name)} " if element.name else ""
    return f"{name}UNIQUE ({cols})"


@compiles(TextClause, "sqlite")
def compile_text_sqlite(element, compiler, **kw):
    return element.text.replace("::jsonb", "")


@pytest.fixture(scope="session")
def review_db_engine():
    """In-memory SQLite engine with JSONB and UUID compatibility helpers."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def register_sqlite_helpers(dbapi_connection, connection_record):
        def jsonb_typeof(val):
            if val is None:
                return None
            try:
                parsed = json.loads(val) if isinstance(val, str) else val
                if isinstance(parsed, dict):
                    return "object"
                if isinstance(parsed, list):
                    return "array"
                if isinstance(parsed, str):
                    return "string"
                if isinstance(parsed, (int, float)):
                    return "number"
                if isinstance(parsed, bool):
                    return "boolean"
                return "null"
            except Exception:
                return "null"

        def jsonb_array_length(val):
            if val is None:
                return 0
            try:
                parsed = json.loads(val) if isinstance(val, str) else val
                return len(parsed) if isinstance(parsed, list) else 0
            except Exception:
                return 0

        dbapi_connection.create_function("jsonb_typeof", 1, jsonb_typeof)
        dbapi_connection.create_function("jsonb_array_length", 1, jsonb_array_length)
        dbapi_connection.create_function("gen_random_uuid", 0, lambda: str(uuid.uuid4()))

    Base.metadata.create_all(engine)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def db_session(review_db_engine):
    """Isolated session per test using a transaction rollback."""
    connection = review_db_engine.connect()
    transaction = connection.begin()
    connection.exec_driver_sql("BEGIN")
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(db_session):
    """FastAPI TestClient with overridden get_db dependency."""
    app.dependency_overrides[get_db] = lambda: db_session
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


def make_test_data(db: Session):
    """Seed test users, category, questions, exam, and attempt."""
    instructor = User(
        id=uuid.uuid4(),
        email="instructor_rev@example.com",
        password_hash="fakehash",
        full_name="Thầy Giáo Dev",
        role=UserRole.INSTRUCTOR,
    )
    student1 = User(
        id=uuid.uuid4(),
        email="student1_rev@example.com",
        password_hash="fakehash",
        full_name="Nguyễn Văn A",
        role=UserRole.STUDENT,
    )
    student2 = User(
        id=uuid.uuid4(),
        email="student2_rev@example.com",
        password_hash="fakehash",
        full_name="Trần Thị B",
        role=UserRole.STUDENT,
    )
    category = Category(
        id=uuid.uuid4(),
        name="Quản trị Dự án Phần mềm",
        created_by=instructor.id,
    )
    now = datetime.now(timezone.utc)
    exam = Exam(
        id=uuid.uuid4(),
        exam_code="PM2026",
        title="Kiểm tra Quản trị Dự án Sprint 1",
        instructor_id=instructor.id,
        duration_minutes=45,
        start_time=now - timedelta(hours=1),
        end_time=now + timedelta(hours=2),
        is_published=True,
    )
    db.add_all([instructor, student1, student2, category, exam])
    db.flush()

    # Question 1: Single choice (Student 1 answered Correctly)
    q1 = Question(
        id=uuid.uuid4(),
        category_id=category.id,
        creator_id=instructor.id,
        content="WBS là gì?",
        question_type=QuestionType.SINGLE_CHOICE,
        cognitive_level=CognitiveLevel.REMEMBER,
        options=[
            {"id": "A", "text": "Phân rã công việc định hướng sản phẩm", "is_correct": True},
            {"id": "B", "text": "Bảng phân bổ ngân sách", "is_correct": False},
        ],
        explanation="WBS là viết tắt của Work Breakdown Structure.",
    )

    # Question 2: Multiple choice (Student 1 answered Incorrectly)
    q2 = Question(
        id=uuid.uuid4(),
        category_id=category.id,
        creator_id=instructor.id,
        content="Nguyên tắc cốt lõi của Scrum?",
        question_type=QuestionType.MULTIPLE_CHOICE,
        cognitive_level=CognitiveLevel.UNDERSTAND,
        options=[
            {"id": "A", "text": "Minh bạch", "is_correct": True},
            {"id": "B", "text": "Thanh tra", "is_correct": True},
            {"id": "C", "text": "Cố định phạm vi", "is_correct": False},
        ],
        explanation="Ba trụ cột của Scrum: Minh bạch, Thanh tra và Thích nghi.",
    )

    # Question 3: True/False (Student 1 did not answer)
    q3 = Question(
        id=uuid.uuid4(),
        category_id=category.id,
        creator_id=instructor.id,
        content="Waterfall phù hợp với yêu cầu thay đổi liên tục?",
        question_type=QuestionType.TRUE_FALSE,
        cognitive_level=CognitiveLevel.APPLY,
        options=[
            {"id": "TRUE", "text": "Đúng", "is_correct": False},
            {"id": "FALSE", "text": "Sai", "is_correct": True},
        ],
        explanation="Waterfall yêu cầu đóng băng phạm vi sớm.",
    )
    db.add_all([q1, q2, q3])
    db.flush()

    # Add ExamQuestions
    eq1 = ExamQuestion(exam_id=exam.id, question_id=q1.id, order_index=1, points=3.0)
    eq2 = ExamQuestion(exam_id=exam.id, question_id=q2.id, order_index=2, points=4.0)
    eq3 = ExamQuestion(exam_id=exam.id, question_id=q3.id, order_index=3, points=3.0)
    db.add_all([eq1, eq2, eq3])
    db.flush()

    # Create completed attempt for student 1 with shuffled snapshot
    snapshot = {
        "version": 1,
        "questions": [
            {"question_id": str(q2.id), "options_order": ["C", "B", "A"]},  # q2 first
            {"question_id": str(q1.id), "options_order": ["B", "A"]},        # q1 second
            {"question_id": str(q3.id), "options_order": ["FALSE", "TRUE"]}, # q3 third
        ],
    }
    started_at = datetime(2026, 11, 1, 8, 0, 0, tzinfo=timezone.utc)
    expires_at = datetime(2026, 11, 1, 8, 45, 0, tzinfo=timezone.utc)
    submitted_at = datetime(2026, 11, 1, 8, 15, 30, tzinfo=timezone.utc)

    attempt1 = ExamAttempt(
        id=uuid.uuid4(),
        exam_id=exam.id,
        student_id=student1.id,
        attempt_number=1,
        status=AttemptStatus.SUBMITTED,
        started_at=started_at,
        expires_at=expires_at,
        submitted_at=submitted_at,
        score=3.0,
        question_order_snapshot=snapshot,
    )
    db.add(attempt1)
    db.flush()

    # Answers: q1 is correct, q2 is wrong, q3 unanswered
    ans1 = AttemptAnswer(
        attempt_id=attempt1.id,
        question_id=q1.id,
        selected_options=["A"],
        is_correct=True,
        points_awarded=3.0,
    )
    ans2 = AttemptAnswer(
        attempt_id=attempt1.id,
        question_id=q2.id,
        selected_options=["C"],
        is_correct=False,
        points_awarded=0.0,
    )
    db.add_all([ans1, ans2])
    db.commit()

    return instructor, student1, student2, exam, q1, q2, q3, attempt1


def test_review_service_and_snapshot_ordering(db_session):
    """Test get_exam_review_data preserves snapshot question order and options order."""
    instructor, student1, _, exam, q1, q2, q3, attempt1 = make_test_data(db_session)

    data = get_exam_review_data(db_session, attempt1.id, current_user=student1)

    assert data["attempt_id"] == str(attempt1.id)
    assert data["exam_title"] == "Kiểm tra Quản trị Dự án Sprint 1"
    assert data["student_name"] == "Nguyễn Văn A"
    assert data["score"] == 3.0
    assert data["total_questions"] == 3
    assert data["correct_count"] == 1
    assert data["incorrect_count"] == 2
    assert data["time_spent_seconds"] == 930  # 15m 30s

    questions = data["questions_review"]
    assert len(questions) == 3

    # Snapshot ordered q2 first, q1 second, q3 third
    assert questions[0]["question_id"] == str(q2.id)
    assert questions[0]["is_correct"] is False
    assert questions[0]["selected_options"] == ["C"]
    assert questions[0]["correct_options"] == ["A", "B"]
    # Check q2 options order is ["C", "B", "A"]
    assert [opt["id"] for opt in questions[0]["options"]] == ["C", "B", "A"]

    assert questions[1]["question_id"] == str(q1.id)
    assert questions[1]["is_correct"] is True
    assert questions[1]["selected_options"] == ["A"]
    assert questions[1]["correct_options"] == ["A"]
    assert [opt["id"] for opt in questions[1]["options"]] == ["B", "A"]

    # Question 3 was unanswered
    assert questions[2]["question_id"] == str(q3.id)
    assert questions[2]["is_correct"] is False
    assert questions[2]["selected_options"] == []
    assert questions[2]["correct_options"] == ["FALSE"]


def test_review_not_found(client, db_session):
    """Non-existent attempt ID returns 404."""
    instructor, _, _, _, _, _, _, _ = make_test_data(db_session)
    token = create_access_token({"sub": str(instructor.id), "role": instructor.role.value})

    resp = client.get(
        f"/api/v1/tutor-analytics/review/{uuid.uuid4()}",
        cookies={"access_token": token},
    )
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


def test_review_in_progress_attempt_rejected(client, db_session):
    """Attempt that is still IN_PROGRESS cannot be reviewed (HTTP 400)."""
    _, _, student2, exam, _, _, _, _ = make_test_data(db_session)

    now = datetime.now(timezone.utc)
    in_progress_attempt = ExamAttempt(
        id=uuid.uuid4(),
        exam_id=exam.id,
        student_id=student2.id,
        attempt_number=1,
        status=AttemptStatus.IN_PROGRESS,
        started_at=now,
        expires_at=now + timedelta(minutes=45),
        question_order_snapshot={"version": 1, "questions": []},
    )
    db_session.add(in_progress_attempt)
    db_session.commit()

    token = create_access_token({"sub": str(student2.id), "role": student2.role.value})
    resp = client.get(
        f"/api/v1/tutor-analytics/review/{in_progress_attempt.id}",
        cookies={"access_token": token},
    )
    assert resp.status_code == 400
    assert "chưa được nộp" in resp.json()["detail"]


def test_review_student_forbidden_other_student_attempt(client, db_session):
    """Student cannot view another student's exam attempt review (HTTP 403)."""
    _, _, student2, _, _, _, _, attempt1 = make_test_data(db_session)

    # Student 2 tries to review Student 1's attempt
    token2 = create_access_token({"sub": str(student2.id), "role": student2.role.value})
    resp = client.get(
        f"/api/v1/tutor-analytics/review/{attempt1.id}",
        cookies={"access_token": token2},
    )
    assert resp.status_code == 403
    assert "không có quyền" in resp.json()["detail"]


def test_review_instructor_can_access_any_attempt(client, db_session):
    """Instructor has permission to view review data of any student's attempt."""
    instructor, _, _, _, _, _, _, attempt1 = make_test_data(db_session)

    token = create_access_token({"sub": str(instructor.id), "role": instructor.role.value})
    resp = client.get(
        f"/api/v1/tutor-analytics/review/{attempt1.id}",
        cookies={"access_token": token},
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["attempt_id"] == str(attempt1.id)
    assert data["score"] == 3.0
    assert data["correct_count"] == 1
    assert data["total_questions"] == 3


def test_review_fallback_order_when_no_snapshot(db_session):
    """When question_order_snapshot is empty, fallback to ExamQuestion.order_index."""
    _, _, _, exam, q1, q2, q3, _ = make_test_data(db_session)

    fresh_student = User(
        id=uuid.uuid4(),
        email="fresh_student@example.com",
        password_hash="fakehash",
        full_name="Lê Văn C",
        role=UserRole.STUDENT,
    )
    db_session.add(fresh_student)
    db_session.flush()

    now = datetime.now(timezone.utc)
    attempt_no_snap = ExamAttempt(
        id=uuid.uuid4(),
        exam_id=exam.id,
        student_id=fresh_student.id,
        attempt_number=1,
        status=AttemptStatus.SUBMITTED,
        started_at=now,
        expires_at=now + timedelta(minutes=45),
        submitted_at=now,
        score=10.0,
        question_order_snapshot={"version": 1, "questions": []},
    )
    db_session.add(attempt_no_snap)
    db_session.commit()

    data = get_exam_review_data(db_session, attempt_no_snap.id, current_user=fresh_student)
    questions = data["questions_review"]
    assert len(questions) == 3
    # Default order_index: q1 (1), q2 (2), q3 (3)
    assert questions[0]["question_id"] == str(q1.id)
    assert questions[1]["question_id"] == str(q2.id)
    assert questions[2]["question_id"] == str(q3.id)
