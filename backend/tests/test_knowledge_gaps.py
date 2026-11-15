"""Tests for AI Tutor Knowledge Gap Diagnostic Card (Issue #17, WBS 5.2.2).

Validates:
- Endpoint GET /api/v1/tutor-analytics/knowledge-gaps/{attempt_id}
- Service diagnose_knowledge_gaps
- Acceptance Criteria 1: "Chủ đề bạn cần củng cố: Kế thừa & Đa hình trong OOP"
- Acceptance Criteria 2: Proposes at least 2 concrete actionable study recommendations
- Handling of 100% correct score (no knowledge gaps)
- State and authorization validations (400 on IN_PROGRESS, 403 on other student, 404 on not found)
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
from app.modules.tutor_analytics.services.knowledge_gap_service import (
    diagnose_knowledge_gaps,
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
def gap_db_engine():
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
def db_session(gap_db_engine):
    """Isolated session per test using a transaction rollback."""
    connection = gap_db_engine.connect()
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


def make_test_environment(db: Session):
    """Seed test instructor, students, category, exam, questions, and attempt."""
    instructor = User(
        id=uuid.uuid4(),
        email="instructor_oop@example.com",
        password_hash="fakehash",
        full_name="Thầy Giáo OOP",
        role=UserRole.INSTRUCTOR,
    )
    student1 = User(
        id=uuid.uuid4(),
        email="student1_oop@example.com",
        password_hash="fakehash",
        full_name="Sinh Viên Nam",
        role=UserRole.STUDENT,
    )
    student2 = User(
        id=uuid.uuid4(),
        email="student2_oop@example.com",
        password_hash="fakehash",
        full_name="Sinh Viên Nữ",
        role=UserRole.STUDENT,
    )
    category = Category(
        id=uuid.uuid4(),
        name="Lập trình Hướng đối tượng OOP",
        created_by=instructor.id,
    )
    now = datetime.now(timezone.utc)
    exam = Exam(
        id=uuid.uuid4(),
        exam_code="OOP2026",
        title="Kiểm tra Lập trình Hướng Đối Tượng",
        instructor_id=instructor.id,
        duration_minutes=60,
        start_time=now - timedelta(hours=1),
        end_time=now + timedelta(hours=3),
        is_published=True,
    )
    db.add_all([instructor, student1, student2, category, exam])
    db.flush()

    # Question 1: Tagged "Kế thừa & Đa hình trong OOP" (Student 1 answered WRONG)
    q1 = Question(
        id=uuid.uuid4(),
        category_id=category.id,
        creator_id=instructor.id,
        content="Trong C++, hàm ảo (virtual function) phục vụ tính chất nào?",
        question_type=QuestionType.SINGLE_CHOICE,
        cognitive_level=CognitiveLevel.UNDERSTAND,
        options=[
            {"id": "A", "text": "Tính đa hình động (Runtime Polymorphism)", "is_correct": True},
            {"id": "B", "text": "Tính đóng gói (Encapsulation)", "is_correct": False},
        ],
        tags=["Kế thừa & Đa hình trong OOP"],
        explanation="Hàm ảo cho phép đa hình động thông qua bảng vtable.",
    )

    # Question 2: Tagged "Kế thừa & Đa hình trong OOP" (Student 1 answered WRONG)
    q2 = Question(
        id=uuid.uuid4(),
        category_id=category.id,
        creator_id=instructor.id,
        content="Từ khóa nào ngăn chặn một lớp kế thừa từ lớp cha trong Java/C#?",
        question_type=QuestionType.SINGLE_CHOICE,
        cognitive_level=CognitiveLevel.REMEMBER,
        options=[
            {"id": "A", "text": "final / sealed", "is_correct": True},
            {"id": "B", "text": "abstract", "is_correct": False},
        ],
        tags=["Kế thừa & Đa hình trong OOP"],
        explanation="Lớp final hoặc sealed không cho phép kế thừa tiếp.",
    )

    # Question 3: Tagged "Design Patterns" (Student 1 answered CORRECT)
    q3 = Question(
        id=uuid.uuid4(),
        category_id=category.id,
        creator_id=instructor.id,
        content="Pattern nào đảm bảo một lớp chỉ có một thể hiện duy nhất?",
        question_type=QuestionType.SINGLE_CHOICE,
        cognitive_level=CognitiveLevel.APPLY,
        options=[
            {"id": "A", "text": "Singleton Pattern", "is_correct": True},
            {"id": "B", "text": "Factory Pattern", "is_correct": False},
        ],
        tags=["Design Patterns"],
        explanation="Singleton kiểm soát khởi tạo đối tượng duy nhất.",
    )
    db.add_all([q1, q2, q3])
    db.flush()

    eq1 = ExamQuestion(exam_id=exam.id, question_id=q1.id, order_index=1, points=3.0)
    eq2 = ExamQuestion(exam_id=exam.id, question_id=q2.id, order_index=2, points=3.0)
    eq3 = ExamQuestion(exam_id=exam.id, question_id=q3.id, order_index=3, points=4.0)
    db.add_all([eq1, eq2, eq3])
    db.flush()

    # Attempt 1 for student1: SUBMITTED
    snapshot = {
        "version": 1,
        "questions": [
            {"question_id": str(q1.id), "options_order": ["A", "B"]},
            {"question_id": str(q2.id), "options_order": ["A", "B"]},
            {"question_id": str(q3.id), "options_order": ["A", "B"]},
        ],
    }
    attempt1 = ExamAttempt(
        id=uuid.uuid4(),
        exam_id=exam.id,
        student_id=student1.id,
        attempt_number=1,
        status=AttemptStatus.SUBMITTED,
        started_at=now - timedelta(minutes=40),
        expires_at=now + timedelta(minutes=20),
        submitted_at=now - timedelta(minutes=5),
        score=4.0,
        question_order_snapshot=snapshot,
    )
    db.add(attempt1)
    db.flush()

    # Answers: q1 wrong, q2 wrong, q3 correct
    ans1 = AttemptAnswer(
        attempt_id=attempt1.id,
        question_id=q1.id,
        selected_options=["B"],
        is_correct=False,
        points_awarded=0.0,
    )
    ans2 = AttemptAnswer(
        attempt_id=attempt1.id,
        question_id=q2.id,
        selected_options=["B"],
        is_correct=False,
        points_awarded=0.0,
    )
    ans3 = AttemptAnswer(
        attempt_id=attempt1.id,
        question_id=q3.id,
        selected_options=["A"],
        is_correct=True,
        points_awarded=4.0,
    )
    db.add_all([ans1, ans2, ans3])
    db.commit()

    return instructor, student1, student2, exam, q1, q2, q3, attempt1


def test_diagnose_knowledge_gaps_success(db_session, client):
    """Verify Issue #17 Acceptance Criteria:
    - Summary headline displays: 'Chủ đề bạn cần củng cố: Kế thừa & Đa hình trong OOP'
    - Proposes at least 2 concrete advice suggestions
    - Accurate statistics on weak topics
    """
    instructor, student1, _, exam, q1, q2, q3, attempt1 = make_test_environment(db_session)

    # 1. Direct Service Call
    data = diagnose_knowledge_gaps(db_session, attempt1.id, current_user=student1)

    assert data["has_gaps"] is True
    assert data["total_wrong"] == 2
    assert data["total_questions"] == 3
    assert data["primary_weak_topic"] == "Kế thừa & Đa hình trong OOP"
    assert data["summary_headline"] == "Chủ đề bạn cần củng cố: Kế thừa & Đa hình trong OOP"

    # Check Acceptance Criteria 2: at least 2 concrete recommendations
    assert len(data["advice"]) >= 2
    for advice in data["advice"]:
        assert len(advice["title"]) > 0
        assert len(advice["description"]) > 0
        assert advice["priority"] in ["HIGH", "MEDIUM"]

    # Check weak topics item
    assert len(data["weak_topics"]) == 1
    weak = data["weak_topics"][0]
    assert weak["topic"] == "Kế thừa & Đa hình trong OOP"
    assert weak["wrong_count"] == 2
    assert weak["total_questions"] == 2
    assert weak["accuracy_percentage"] == 0.0

    # 2. HTTP Endpoint Call
    token = create_access_token({"sub": str(student1.id), "role": student1.role.value})
    resp = client.get(
        f"/api/v1/tutor-analytics/knowledge-gaps/{attempt1.id}",
        cookies={"access_token": token},
    )
    assert resp.status_code == 200
    res_data = resp.json()["data"]
    assert res_data["summary_headline"] == "Chủ đề bạn cần củng cố: Kế thừa & Đa hình trong OOP"
    assert len(res_data["advice"]) >= 2


def test_diagnose_perfect_score_no_gaps(db_session, client):
    """Verify behavior when student answers 100% correctly (no knowledge gaps)."""
    instructor, _, student2, exam, q1, q2, q3, _ = make_test_environment(db_session)

    now = datetime.now(timezone.utc)
    perfect_attempt = ExamAttempt(
        id=uuid.uuid4(),
        exam_id=exam.id,
        student_id=student2.id,
        attempt_number=1,
        status=AttemptStatus.SUBMITTED,
        started_at=now - timedelta(minutes=30),
        expires_at=now + timedelta(minutes=30),
        submitted_at=now,
        score=10.0,
        question_order_snapshot={"version": 1, "questions": [
            {"question_id": str(q1.id), "options_order": ["A", "B"]},
            {"question_id": str(q2.id), "options_order": ["A", "B"]},
            {"question_id": str(q3.id), "options_order": ["A", "B"]},
        ]},
    )
    db_session.add(perfect_attempt)
    db_session.flush()

    # All answers correct
    db_session.add_all([
        AttemptAnswer(attempt_id=perfect_attempt.id, question_id=q1.id, selected_options=["A"], is_correct=True, points_awarded=3.0),
        AttemptAnswer(attempt_id=perfect_attempt.id, question_id=q2.id, selected_options=["A"], is_correct=True, points_awarded=3.0),
        AttemptAnswer(attempt_id=perfect_attempt.id, question_id=q3.id, selected_options=["A"], is_correct=True, points_awarded=4.0),
    ])
    db_session.commit()

    token = create_access_token({"sub": str(student2.id), "role": student2.role.value})
    resp = client.get(
        f"/api/v1/tutor-analytics/knowledge-gaps/{perfect_attempt.id}",
        cookies={"access_token": token},
    )
    assert resp.status_code == 200
    res_data = resp.json()["data"]
    assert res_data["has_gaps"] is False
    assert res_data["total_wrong"] == 0
    assert len(res_data["weak_topics"]) == 0
    assert len(res_data["advice"]) >= 2
    assert "không có lỗ hổng kiến thức" in res_data["summary_headline"].lower()


def test_diagnose_not_found(client, db_session):
    """404 when attempt_id does not exist."""
    instructor, _, _, _, _, _, _, _ = make_test_environment(db_session)
    token = create_access_token({"sub": str(instructor.id), "role": instructor.role.value})

    resp = client.get(
        f"/api/v1/tutor-analytics/knowledge-gaps/{uuid.uuid4()}",
        cookies={"access_token": token},
    )
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


def test_diagnose_in_progress_attempt_rejected(client, db_session):
    """400 when attempt is still IN_PROGRESS."""
    _, _, student2, exam, _, _, _, _ = make_test_environment(db_session)

    now = datetime.now(timezone.utc)
    in_prog_attempt = ExamAttempt(
        id=uuid.uuid4(),
        exam_id=exam.id,
        student_id=student2.id,
        attempt_number=1,
        status=AttemptStatus.IN_PROGRESS,
        started_at=now,
        expires_at=now + timedelta(minutes=45),
        question_order_snapshot={"version": 1, "questions": []},
    )
    db_session.add(in_prog_attempt)
    db_session.commit()

    token = create_access_token({"sub": str(student2.id), "role": student2.role.value})
    resp = client.get(
        f"/api/v1/tutor-analytics/knowledge-gaps/{in_prog_attempt.id}",
        cookies={"access_token": token},
    )
    assert resp.status_code == 400
    assert "chưa được nộp" in resp.json()["detail"]


def test_diagnose_student_forbidden_other_attempt(client, db_session):
    """403 when student attempts to view another student's diagnostic."""
    _, _, student2, _, _, _, _, attempt1 = make_test_environment(db_session)

    token2 = create_access_token({"sub": str(student2.id), "role": student2.role.value})
    resp = client.get(
        f"/api/v1/tutor-analytics/knowledge-gaps/{attempt1.id}",
        cookies={"access_token": token2},
    )
    assert resp.status_code == 403
    assert "không có quyền" in resp.json()["detail"]


def test_diagnose_instructor_can_access_any_attempt(client, db_session):
    """200 when instructor views student's diagnostic."""
    instructor, _, _, _, _, _, _, attempt1 = make_test_environment(db_session)

    inst_token = create_access_token({"sub": str(instructor.id), "role": instructor.role.value})
    resp = client.get(
        f"/api/v1/tutor-analytics/knowledge-gaps/{attempt1.id}",
        cookies={"access_token": inst_token},
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["primary_weak_topic"] == "Kế thừa & Đa hình trong OOP"
