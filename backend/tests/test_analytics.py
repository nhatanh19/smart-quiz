"""Tests for Learning Analytics & Score Distribution Dashboard (Issue #36, WBS 5.3.1 & 5.3.2).

Validates:
- Endpoint GET /api/v1/tutor-analytics/analytics/student/{student_id} (Student progress & mastery)
- Endpoint GET /api/v1/tutor-analytics/analytics/exam/{exam_id} (Lecturer score distribution & histogram)
- Endpoint GET /api/v1/tutor-analytics/analytics/exam/{exam_id}/csv (CSV scoresheet export)
- Endpoint GET /api/v1/tutor-analytics/analytics/instructor/exams (Accessible exams list)
- RBAC / Ownership enforcement:
  * Student cannot view other students' analytics (403)
  * Student cannot view class exam distribution (403)
  * Instructor can only view exams they own (403 for other instructors' exams)
  * Admin can view everything
- Calculation correctness:
  * Score trends, average, highest, lowest, pass rate
  * Topic accuracy percentage and mastery tiers
  * Score distribution histogram bins (0-1, 1-2, ..., 9-10)
  * Top difficult questions calculation
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
def analytics_db_engine():
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
def db_session(analytics_db_engine):
    """Isolated session per test using a transaction rollback."""
    connection = analytics_db_engine.connect()
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
        app.dependency_overrides.pop(get_db, None)


def auth_cookie(user: User) -> dict:
    token = create_access_token(
        data={"sub": str(user.id), "role": user.role.value, "email": user.email}
    )
    return {"access_token": token}


# ==============================================================================
# FIXTURES SETUP
# ==============================================================================


@pytest.fixture
def seed_data(db_session: Session):
    # Instructors
    instructor_1 = User(
        id=uuid.uuid4(),
        email="instructor1@quiz.edu.vn",
        password_hash="hash",
        full_name="TS. Nguyễn Văn A",
        role=UserRole.INSTRUCTOR,
        is_active=True,
    )
    instructor_2 = User(
        id=uuid.uuid4(),
        email="instructor2@quiz.edu.vn",
        password_hash="hash",
        full_name="TS. Trần Văn B",
        role=UserRole.INSTRUCTOR,
        is_active=True,
    )
    # Admin
    admin_user = User(
        id=uuid.uuid4(),
        email="admin@quiz.edu.vn",
        password_hash="hash",
        full_name="Quản Trị Viên",
        role=UserRole.ADMIN,
        is_active=True,
    )
    # Students
    student_1 = User(
        id=uuid.uuid4(),
        email="student1@quiz.edu.vn",
        password_hash="hash",
        full_name="Lê Thị C",
        role=UserRole.STUDENT,
        is_active=True,
    )
    student_2 = User(
        id=uuid.uuid4(),
        email="student2@quiz.edu.vn",
        password_hash="hash",
        full_name="Phạm Văn D",
        role=UserRole.STUDENT,
        is_active=True,
    )

    db_session.add_all([instructor_1, instructor_2, admin_user, student_1, student_2])
    db_session.flush()

    # Categories
    cat_oop = Category(
        id=uuid.uuid4(),
        name="Lập trình hướng đối tượng",
        created_by=instructor_1.id,
    )
    cat_db = Category(
        id=uuid.uuid4(),
        name="Cơ sở dữ liệu",
        created_by=instructor_1.id,
    )
    db_session.add_all([cat_oop, cat_db])
    db_session.flush()

    # Questions
    q1 = Question(
        id=uuid.uuid4(),
        category_id=cat_oop.id,
        creator_id=instructor_1.id,
        content="Đa hình trong OOP là gì?",
        question_type=QuestionType.SINGLE_CHOICE,
        cognitive_level=CognitiveLevel.UNDERSTAND,
        options=[
            {"id": "A", "text": "Một giao diện nhiều hành vi", "is_correct": True},
            {"id": "B", "text": "Đóng gói dữ liệu", "is_correct": False},
        ],
        tags=["oop", "polymorphism"],
    )
    q2 = Question(
        id=uuid.uuid4(),
        category_id=cat_db.id,
        creator_id=instructor_1.id,
        content="Khóa chính (Primary Key) có thể chứa NULL không?",
        question_type=QuestionType.TRUE_FALSE,
        cognitive_level=CognitiveLevel.REMEMBER,
        options=[
            {"id": "A", "text": "Đúng", "is_correct": False},
            {"id": "B", "text": "Sai", "is_correct": True},
        ],
        tags=["database", "sql"],
    )
    db_session.add_all([q1, q2])
    db_session.flush()

    # Exam created by instructor 1
    exam = Exam(
        id=uuid.uuid4(),
        exam_code="OOPDB01",
        title="Kiểm tra giữa kỳ OOP & DB",
        instructor_id=instructor_1.id,
        duration_minutes=45,
        max_attempts=2,
    )
    # Exam created by instructor 2
    other_exam = Exam(
        id=uuid.uuid4(),
        exam_code="OTHER99",
        title="Đề thi của Giảng viên 2",
        instructor_id=instructor_2.id,
        duration_minutes=60,
    )
    db_session.add_all([exam, other_exam])
    db_session.flush()

    eq1 = ExamQuestion(id=uuid.uuid4(), exam_id=exam.id, question_id=q1.id, order_index=1, points=5.0)
    eq2 = ExamQuestion(id=uuid.uuid4(), exam_id=exam.id, question_id=q2.id, order_index=2, points=5.0)
    db_session.add_all([eq1, eq2])
    db_session.flush()

    now = datetime.now(timezone.utc)

    # Attempt 1 for Student 1: Score 10.0 (both correct)
    att1 = ExamAttempt(
        id=uuid.uuid4(),
        exam_id=exam.id,
        student_id=student_1.id,
        attempt_number=1,
        started_at=now - timedelta(minutes=40),
        expires_at=now + timedelta(minutes=5),
        submitted_at=now - timedelta(minutes=10),
        score=10.0,
        status=AttemptStatus.SUBMITTED,
        violation_count=0,
        question_order_snapshot={"version": 1, "questions": [{"question_id": str(q1.id)}, {"question_id": str(q2.id)}]},
    )
    db_session.add(att1)
    db_session.flush()

    ans1_1 = AttemptAnswer(id=uuid.uuid4(), attempt_id=att1.id, question_id=q1.id, selected_options=["A"], is_correct=True, points_awarded=5.0)
    ans1_2 = AttemptAnswer(id=uuid.uuid4(), attempt_id=att1.id, question_id=q2.id, selected_options=["B"], is_correct=True, points_awarded=5.0)
    db_session.add_all([ans1_1, ans1_2])

    # Attempt 2 for Student 2: Score 5.0 (q1 wrong, q2 correct)
    att2 = ExamAttempt(
        id=uuid.uuid4(),
        exam_id=exam.id,
        student_id=student_2.id,
        attempt_number=1,
        started_at=now - timedelta(minutes=30),
        expires_at=now + timedelta(minutes=15),
        submitted_at=now - timedelta(minutes=5),
        score=5.0,
        status=AttemptStatus.SUBMITTED,
        violation_count=1,
        question_order_snapshot={"version": 1, "questions": [{"question_id": str(q1.id)}, {"question_id": str(q2.id)}]},
    )
    db_session.add(att2)
    db_session.flush()

    ans2_1 = AttemptAnswer(id=uuid.uuid4(), attempt_id=att2.id, question_id=q1.id, selected_options=["B"], is_correct=False, points_awarded=0.0)
    ans2_2 = AttemptAnswer(id=uuid.uuid4(), attempt_id=att2.id, question_id=q2.id, selected_options=["B"], is_correct=True, points_awarded=5.0)
    db_session.add_all([ans2_1, ans2_2])

    db_session.commit()

    return {
        "instructor_1": instructor_1,
        "instructor_2": instructor_2,
        "admin": admin_user,
        "student_1": student_1,
        "student_2": student_2,
        "cat_oop": cat_oop,
        "cat_db": cat_db,
        "q1": q1,
        "q2": q2,
        "exam": exam,
        "other_exam": other_exam,
        "att1": att1,
        "att2": att2,
    }


# ==============================================================================
# STUDENT ANALYTICS TESTS
# ==============================================================================


def test_student_analytics_own_profile(client, seed_data):
    """Student can view their own analytics."""
    s1 = seed_data["student_1"]
    resp = client.get(
        f"/api/v1/tutor-analytics/analytics/student/{s1.id}",
        cookies=auth_cookie(s1),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    data = body["data"]

    assert data["student_id"] == str(s1.id)
    assert data["student_name"] == s1.full_name
    assert data["summary"]["total_attempts"] == 1
    assert data["summary"]["average_score"] == 10.0
    assert data["summary"]["highest_score"] == 10.0
    assert data["summary"]["pass_rate"] == 100.0

    # Trends
    assert len(data["trends"]) == 1
    assert data["trends"][0]["score"] == 10.0

    # Topic Mastery: OOP (100%), DB (100%)
    topics = {t["category_name"]: t for t in data["topics_mastery"]}
    assert "Lập trình hướng đối tượng" in topics
    assert topics["Lập trình hướng đối tượng"]["accuracy_percentage"] == 100.0
    assert topics["Lập trình hướng đối tượng"]["mastery_level"] == "EXCELLENT"


def test_student_analytics_special_me_path(client, seed_data):
    """Student can view analytics using /analytics/student/me."""
    s1 = seed_data["student_1"]
    resp = client.get(
        "/api/v1/tutor-analytics/analytics/student/me",
        cookies=auth_cookie(s1),
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["student_id"] == str(s1.id)


def test_student_analytics_forbidden_other_student(client, seed_data):
    """Student cannot view another student's analytics (403)."""
    s1 = seed_data["student_1"]
    s2 = seed_data["student_2"]
    resp = client.get(
        f"/api/v1/tutor-analytics/analytics/student/{s2.id}",
        cookies=auth_cookie(s1),
    )
    assert resp.status_code == 403


def test_student_analytics_instructor_and_admin_allowed(client, seed_data):
    """Instructor and Admin can view any student's analytics."""
    s2 = seed_data["student_2"]
    inst1 = seed_data["instructor_1"]
    adm = seed_data["admin"]

    resp1 = client.get(
        f"/api/v1/tutor-analytics/analytics/student/{s2.id}",
        cookies=auth_cookie(inst1),
    )
    assert resp1.status_code == 200
    assert resp1.json()["data"]["student_name"] == s2.full_name

    resp2 = client.get(
        f"/api/v1/tutor-analytics/analytics/student/{s2.id}",
        cookies=auth_cookie(adm),
    )
    assert resp2.status_code == 200


def test_student_analytics_knowledge_gaps(client, seed_data):
    """Student 2 has wrong answer in OOP -> knowledge gap identified."""
    s2 = seed_data["student_2"]
    resp = client.get(
        f"/api/v1/tutor-analytics/analytics/student/{s2.id}",
        cookies=auth_cookie(s2),
    )
    assert resp.status_code == 200
    data = resp.json()["data"]

    # Student 2 answered q1 (OOP) wrong -> accuracy 0%
    gaps = data["knowledge_gaps"]
    assert len(gaps) >= 1
    assert any(g["category_name"] == "Lập trình hướng đối tượng" for g in gaps)


def test_student_analytics_invalid_uuid(client, seed_data):
    s1 = seed_data["student_1"]
    resp = client.get(
        "/api/v1/tutor-analytics/analytics/student/not-a-valid-uuid",
        cookies=auth_cookie(s1),
    )
    assert resp.status_code == 400


# ==============================================================================
# EXAM ANALYTICS TESTS
# ==============================================================================


def test_exam_analytics_instructor_owner(client, seed_data):
    """Instructor owner can view score distribution & statistics."""
    inst1 = seed_data["instructor_1"]
    exam = seed_data["exam"]

    resp = client.get(
        f"/api/v1/tutor-analytics/analytics/exam/{exam.id}",
        cookies=auth_cookie(inst1),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    data = body["data"]

    assert data["exam_id"] == str(exam.id)
    assert data["exam_code"] == exam.exam_code
    assert data["total_questions"] == 2

    # Summary: 2 attempts, scores: 10.0, 5.0
    summary = data["summary"]
    assert summary["total_attempts"] == 2
    assert summary["total_students"] == 2
    assert summary["min_score"] == 5.0
    assert summary["max_score"] == 10.0
    assert summary["avg_score"] == 7.5
    assert summary["pass_count"] == 2
    assert summary["pass_rate"] == 100.0

    # Score distribution: 10 bins
    assert len(data["score_distribution"]) == 10
    # Bin for score 5.0 is index 5 ("5 - <6")
    bin_5 = data["score_distribution"][5]
    assert bin_5["count"] == 1
    # Bin for score 10.0 is index 9 ("9 - 10")
    bin_10 = data["score_distribution"][9]
    assert bin_10["count"] == 1

    # Difficult questions: q1 had 1 wrong response out of 2 -> 50% incorrect
    assert len(data["difficult_questions"]) >= 1
    top_q = data["difficult_questions"][0]
    assert top_q["content"] == "Đa hình trong OOP là gì?"
    assert top_q["wrong_count"] == 1
    assert top_q["incorrect_rate"] == 50.0

    # Student scores list
    assert len(data["student_scores"]) == 2
    scores_vals = [s["score"] for s in data["student_scores"]]
    assert 10.0 in scores_vals
    assert 5.0 in scores_vals


def test_exam_analytics_admin_access(client, seed_data):
    """Admin can view analytics for any exam."""
    adm = seed_data["admin"]
    exam = seed_data["exam"]

    resp = client.get(
        f"/api/v1/tutor-analytics/analytics/exam/{exam.id}",
        cookies=auth_cookie(adm),
    )
    assert resp.status_code == 200


def test_exam_analytics_forbidden_for_other_instructor(client, seed_data):
    """Instructor cannot view analytics for an exam owned by another instructor (403)."""
    inst2 = seed_data["instructor_2"]
    exam1 = seed_data["exam"]

    resp = client.get(
        f"/api/v1/tutor-analytics/analytics/exam/{exam1.id}",
        cookies=auth_cookie(inst2),
    )
    assert resp.status_code == 403


def test_exam_analytics_forbidden_for_student(client, seed_data):
    """Student cannot view class exam distribution analytics (403)."""
    s1 = seed_data["student_1"]
    exam = seed_data["exam"]

    resp = client.get(
        f"/api/v1/tutor-analytics/analytics/exam/{exam.id}",
        cookies=auth_cookie(s1),
    )
    assert resp.status_code == 403


def test_exam_analytics_not_found(client, seed_data):
    inst1 = seed_data["instructor_1"]
    random_id = uuid.uuid4()
    resp = client.get(
        f"/api/v1/tutor-analytics/analytics/exam/{random_id}",
        cookies=auth_cookie(inst1),
    )
    assert resp.status_code == 404


def test_exam_csv_export(client, seed_data):
    """Lecturer can export exam scores to CSV."""
    inst1 = seed_data["instructor_1"]
    exam = seed_data["exam"]

    resp = client.get(
        f"/api/v1/tutor-analytics/analytics/exam/{exam.id}/csv",
        cookies=auth_cookie(inst1),
    )
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
    assert "attachment" in resp.headers["content-disposition"]
    content = resp.content.decode("utf-8-sig")
    assert "Mã đề thi" in content
    assert exam.exam_code in content
    assert "Lê Thị C" in content
    assert "Phạm Văn D" in content


def test_list_accessible_exams_for_instructor(client, seed_data):
    """Instructor lists their own exams."""
    inst1 = seed_data["instructor_1"]
    resp = client.get(
        "/api/v1/tutor-analytics/analytics/instructor/exams",
        cookies=auth_cookie(inst1),
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 1
    assert data[0]["exam_code"] == "OOPDB01"
