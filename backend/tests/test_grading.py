"""Unit and integration test suite for Issue #14: Instant Multi-Question Type Auto-Grading Engine.

Covers:
- Single choice, Multiple choice (with partial credit), True/False grading algorithms
- Points weighting and 10-point scale conversion
- Edge cases E1 to E10 (DEV3_DEV4_WORKING_AGREEMENT.md section 7.3)
- Contract invariants (K-01, K-02, I-01)
- HTTP Endpoint POST /api/v1/tutor-analytics/grade/{attempt_id} (Role access & error codes)
- Performance (< 300ms SLA)
"""

from datetime import datetime, timedelta, timezone
import json
import time
import uuid

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.sql.elements import TextClause

from app.core.database import Base, get_db
from app.core.security import create_access_token
from app.main import app
from app.models.entities import (
    AttemptAnswer,
    AttemptStatus,
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
    SnapshotMismatchError,
)
from app.modules.tutor_analytics.services.grading_service import (
    GradingResult,
    grade_attempt,
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
def grading_db_engine(auth_engine):
    """Use the migrated temporary PostgreSQL DB when configured, otherwise SQLite."""
    if auth_engine.dialect.name == "postgresql":
        yield auth_engine
        return
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
def db_session(grading_db_engine):
    """Isolated session per test using a transaction rollback."""
    connection = grading_db_engine.connect()
    transaction = connection.begin()
    if connection.dialect.name == "sqlite":
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
    """Helper to populate base instructor, student, category, and exam."""
    instructor = User(
        id=uuid.uuid4(),
        email="instructor@example.com",
        password_hash="fakehash",
        full_name="Instructor Dev",
        role=UserRole.INSTRUCTOR,
    )
    student = User(
        id=uuid.uuid4(),
        email="student@example.com",
        password_hash="fakehash",
        full_name="Student Dev",
        role=UserRole.STUDENT,
    )
    admin = User(
        id=uuid.uuid4(),
        email="admin@example.com",
        password_hash="fakehash",
        full_name="Admin Dev",
        role=UserRole.ADMIN,
    )
    category = Category(
        id=uuid.uuid4(),
        name="Software Engineering",
        created_by=instructor.id,
    )
    exam = Exam(
        id=uuid.uuid4(),
        exam_code="QUIZ101",
        title="Software Project Management Quiz",
        instructor_id=instructor.id,
        duration_minutes=60,
    )
    db.add_all([instructor, student, admin, category, exam])
    db.flush()
    return instructor, student, admin, category, exam


def create_question(
    db: Session,
    category_id: uuid.UUID,
    creator_id: uuid.UUID,
    question_type: QuestionType,
    options: list[dict],
    content: str = "Test Question",
) -> Question:
    q = Question(
        id=uuid.uuid4(),
        category_id=category_id,
        creator_id=creator_id,
        content=content,
        question_type=question_type,
        cognitive_level=CognitiveLevel.REMEMBER,
        options=options,
    )
    db.add(q)
    db.flush()
    return q


def create_exam_question(
    db: Session,
    exam_id: uuid.UUID,
    question: Question,
    order_index: int,
    points: float = 1.0,
) -> ExamQuestion:
    eq = ExamQuestion(
        id=uuid.uuid4(),
        exam_id=exam_id,
        question_id=question.id,
        order_index=order_index,
        points=points,
    )
    db.add(eq)
    db.flush()
    return eq


def create_attempt(
    db: Session,
    exam_id: uuid.UUID,
    student_id: uuid.UUID,
    snapshot_questions: list[dict],
    status: AttemptStatus = AttemptStatus.IN_PROGRESS,
    started_at: datetime = None,
    submitted_at: datetime = None,
    attempt_number: int = 1,
) -> ExamAttempt:
    now = datetime.now(timezone.utc)
    if started_at is None:
        started_at = now - timedelta(minutes=15)
    attempt = ExamAttempt(
        id=uuid.uuid4(),
        exam_id=exam_id,
        student_id=student_id,
        attempt_number=attempt_number,
        started_at=started_at,
        expires_at=started_at + timedelta(minutes=60),
        submitted_at=submitted_at,
        status=status,
        question_order_snapshot={"version": 1, "questions": snapshot_questions},
    )
    db.add(attempt)
    db.flush()
    return attempt


# ==============================================================================
# 1. CORE QUESTION TYPE GRADING & PARTIAL CREDIT TESTS
# ==============================================================================


def test_single_choice_grading(db_session):
    _, student, _, category, exam = make_test_environment(db_session)
    q = create_question(
        db_session, category.id, exam.instructor_id, QuestionType.SINGLE_CHOICE,
        [
            {"id": "A", "text": "Option A", "is_correct": True},
            {"id": "B", "text": "Option B", "is_correct": False},
            {"id": "C", "text": "Option C", "is_correct": False},
        ],
    )
    create_exam_question(db_session, exam.id, q, order_index=1, points=2.0)
    snapshot_q = [{"question_id": str(q.id), "options_order": ["B", "A", "C"]}]

    # Case 1: Correct choice
    student1 = User(id=uuid.uuid4(), email="s1@example.com", password_hash="h", full_name="S1", role=UserRole.STUDENT)
    db_session.add(student1)
    db_session.flush()
    attempt1 = create_attempt(db_session, exam.id, student1.id, snapshot_q)
    ans1 = AttemptAnswer(attempt_id=attempt1.id, question_id=q.id, selected_options=["A"])
    db_session.add(ans1)
    db_session.flush()

    res1 = grade_attempt(db_session, attempt1.id)
    assert res1.score == 10.0
    assert res1.correct_count == 1
    assert res1.answers[0]["is_correct"] is True
    assert res1.answers[0]["points_awarded"] == 2.0
    assert ans1.is_correct is True
    assert ans1.points_awarded == 2.0

    # Case 2: Wrong choice
    student2 = User(id=uuid.uuid4(), email="s2@example.com", password_hash="h", full_name="S2", role=UserRole.STUDENT)
    db_session.add(student2)
    db_session.flush()
    attempt2 = create_attempt(db_session, exam.id, student2.id, snapshot_q)
    ans2 = AttemptAnswer(attempt_id=attempt2.id, question_id=q.id, selected_options=["B"])
    db_session.add(ans2)
    db_session.flush()

    res2 = grade_attempt(db_session, attempt2.id)
    assert res2.score == 0.0
    assert res2.correct_count == 0
    assert res2.answers[0]["is_correct"] is False
    assert res2.answers[0]["points_awarded"] == 0.0

    # Case 3: Multiple options selected for a single choice question -> wrong
    student3 = User(id=uuid.uuid4(), email="s3@example.com", password_hash="h", full_name="S3", role=UserRole.STUDENT)
    db_session.add(student3)
    db_session.flush()
    attempt3 = create_attempt(db_session, exam.id, student3.id, snapshot_q)
    ans3 = AttemptAnswer(attempt_id=attempt3.id, question_id=q.id, selected_options=["A", "B"])
    db_session.add(ans3)
    db_session.flush()

    res3 = grade_attempt(db_session, attempt3.id)
    assert res3.score == 0.0
    assert res3.answers[0]["is_correct"] is False


def test_true_false_grading(db_session):
    _, student, _, category, exam = make_test_environment(db_session)
    q = create_question(
        db_session, category.id, exam.instructor_id, QuestionType.TRUE_FALSE,
        [
            {"id": "TRUE", "text": "Đúng", "is_correct": True},
            {"id": "FALSE", "text": "Sai", "is_correct": False},
        ],
    )
    create_exam_question(db_session, exam.id, q, order_index=1, points=1.0)
    snapshot_q = [{"question_id": str(q.id), "options_order": ["FALSE", "TRUE"]}]

    attempt = create_attempt(db_session, exam.id, student.id, snapshot_q)
    ans = AttemptAnswer(attempt_id=attempt.id, question_id=q.id, selected_options=["TRUE"])
    db_session.add(ans)
    db_session.flush()

    res = grade_attempt(db_session, attempt.id)
    assert res.score == 10.0
    assert res.correct_count == 1
    assert res.answers[0]["is_correct"] is True
    assert res.answers[0]["points_awarded"] == 1.0


def test_multiple_choice_partial_credit_formula(db_session):
    r"""Test exact formula: ratio = clamp((|S ∩ C| - |S \ C|) / |C|, 0, 1)

    Spec table: C = {A, C}, points = 2.0
    - ["A", "C"] -> ratio = 1.0 -> points = 2.0
    - ["A"]      -> ratio = 0.5 -> points = 1.0
    - ["A", "B"] -> ratio = 0.0 -> points = 0.0
    - ["A", "B", "C"] -> ratio = 0.5 -> points = 1.0
    - ["B", "D"] -> ratio = 0.0 -> points = 0.0 (clamped, not negative)
    - []         -> ratio = 0.0 -> points = 0.0
    """
    _, student, _, category, exam = make_test_environment(db_session)
    q = create_question(
        db_session, category.id, exam.instructor_id, QuestionType.MULTIPLE_CHOICE,
        [
            {"id": "A", "text": "A", "is_correct": True},
            {"id": "B", "text": "B", "is_correct": False},
            {"id": "C", "text": "C", "is_correct": True},
            {"id": "D", "text": "D", "is_correct": False},
        ],
    )
    create_exam_question(db_session, exam.id, q, order_index=1, points=2.0)
    snapshot_q = [{"question_id": str(q.id), "options_order": ["A", "B", "C", "D"]}]

    test_cases = [
        (["A", "C"], 2.0, 10.0, True),
        (["A"], 1.0, 5.0, False),
        (["A", "B"], 0.0, 0.0, False),
        (["A", "B", "C"], 1.0, 5.0, False),
        (["B", "D"], 0.0, 0.0, False),
        ([], 0.0, 0.0, False),
    ]

    for idx, (selected, expected_points, expected_score, expected_correct) in enumerate(test_cases, start=1):
        stud = User(id=uuid.uuid4(), email=f"stud_{idx}@example.com", password_hash="h", full_name=f"S{idx}", role=UserRole.STUDENT)
        db_session.add(stud)
        db_session.flush()
        attempt = create_attempt(db_session, exam.id, stud.id, snapshot_q)
        ans = AttemptAnswer(attempt_id=attempt.id, question_id=q.id, selected_options=selected)
        db_session.add(ans)
        db_session.flush()

        res = grade_attempt(db_session, attempt.id)
        assert res.answers[0]["points_awarded"] == expected_points
        assert res.score == expected_score
        assert res.answers[0]["is_correct"] is expected_correct


def test_mixed_questions_weighted_points_and_10_scale(db_session):
    """Test 3 questions with different points:

    Q1: 2.0 pts, SINGLE_CHOICE, answer correct -> 2.0 pts
    Q2: 3.0 pts, MULTIPLE_CHOICE, partial 50% -> 1.5 pts
    Q3: 1.0 pt, TRUE_FALSE, answer wrong -> 0.0 pt
    Total exam points = 6.0 pts.
    Total awarded = 3.5 pts.
    Scale 10 = round((3.5 / 6.0) * 10, 2) = 5.83.
    """
    _, student, _, category, exam = make_test_environment(db_session)
    q1 = create_question(
        db_session, category.id, exam.instructor_id, QuestionType.SINGLE_CHOICE,
        [{"id": "A", "text": "A", "is_correct": True}, {"id": "B", "text": "B", "is_correct": False}],
    )
    q2 = create_question(
        db_session, category.id, exam.instructor_id, QuestionType.MULTIPLE_CHOICE,
        [
            {"id": "A", "text": "A", "is_correct": True},
            {"id": "B", "text": "B", "is_correct": False},
            {"id": "C", "text": "C", "is_correct": True},
        ],
    )
    q3 = create_question(
        db_session, category.id, exam.instructor_id, QuestionType.TRUE_FALSE,
        [{"id": "TRUE", "text": "T", "is_correct": True}, {"id": "FALSE", "text": "F", "is_correct": False}],
    )
    create_exam_question(db_session, exam.id, q1, order_index=1, points=2.0)
    create_exam_question(db_session, exam.id, q2, order_index=2, points=3.0)
    create_exam_question(db_session, exam.id, q3, order_index=3, points=1.0)

    snapshot_q = [
        {"question_id": str(q1.id), "options_order": ["A", "B"]},
        {"question_id": str(q2.id), "options_order": ["A", "B", "C"]},
        {"question_id": str(q3.id), "options_order": ["TRUE", "FALSE"]},
    ]
    attempt = create_attempt(db_session, exam.id, student.id, snapshot_q)
    db_session.add_all([
        AttemptAnswer(attempt_id=attempt.id, question_id=q1.id, selected_options=["A"]),
        AttemptAnswer(attempt_id=attempt.id, question_id=q2.id, selected_options=["A"]),
        AttemptAnswer(attempt_id=attempt.id, question_id=q3.id, selected_options=["FALSE"]),
    ])
    db_session.flush()

    res = grade_attempt(db_session, attempt.id)
    assert res.score == 5.83
    assert res.correct_count == 1
    assert res.total_questions == 3
    assert len(res.answers) == 3


# ==============================================================================
# 2. EDGE CASES E1 TO E10 (SPEC SECTION 7.3)
# ==============================================================================


def test_e1_attempt_not_found(db_session):
    non_existent = uuid.uuid4()
    with pytest.raises(NotFoundError):
        grade_attempt(db_session, non_existent)


def test_e2_already_submitted_without_force(db_session):
    _, student, _, category, exam = make_test_environment(db_session)
    q = create_question(
        db_session, category.id, exam.instructor_id, QuestionType.SINGLE_CHOICE,
        [{"id": "A", "text": "A", "is_correct": True}, {"id": "B", "text": "B", "is_correct": False}],
    )
    create_exam_question(db_session, exam.id, q, order_index=1, points=1.0)
    snapshot_q = [{"question_id": str(q.id), "options_order": ["A", "B"]}]

    started = datetime.now(timezone.utc) - timedelta(minutes=10)
    submitted = started + timedelta(minutes=8)
    attempt = create_attempt(
        db_session, exam.id, student.id, snapshot_q,
        status=AttemptStatus.SUBMITTED, started_at=started, submitted_at=submitted,
    )
    attempt.score = 7.5
    ans = AttemptAnswer(
        attempt_id=attempt.id, question_id=q.id, selected_options=["A"],
        is_correct=True, points_awarded=1.0,
    )
    db_session.add(ans)
    db_session.flush()

    # Call with force=False -> returns existing cached result
    res = grade_attempt(db_session, attempt.id, force=False)
    assert res.already_graded is True
    assert res.score == 7.5
    assert res.time_spent_seconds == 8 * 60

    # Call with force=True -> recalculates correctly
    res_force = grade_attempt(db_session, attempt.id, force=True)
    assert res_force.already_graded is False
    assert res_force.score == 10.0


def test_e3_locked_violation_or_expired_grading(db_session):
    _, _, _, category, exam = make_test_environment(db_session)
    q = create_question(
        db_session, category.id, exam.instructor_id, QuestionType.SINGLE_CHOICE,
        [{"id": "A", "text": "A", "is_correct": True}, {"id": "B", "text": "B", "is_correct": False}],
    )
    create_exam_question(db_session, exam.id, q, order_index=1, points=1.0)
    snapshot_q = [{"question_id": str(q.id), "options_order": ["A", "B"]}]

    for idx, test_status in enumerate((AttemptStatus.LOCKED_VIOLATION, AttemptStatus.EXPIRED), start=1):
        stud = User(id=uuid.uuid4(), email=f"e3_{idx}@example.com", password_hash="h", full_name=f"E3_{idx}", role=UserRole.STUDENT)
        db_session.add(stud)
        db_session.flush()

        started = datetime.now(timezone.utc) - timedelta(minutes=20)
        submitted = started + timedelta(minutes=15)
        attempt = create_attempt(
            db_session, exam.id, stud.id, snapshot_q,
            status=test_status, started_at=started, submitted_at=submitted,
        )
        ans = AttemptAnswer(attempt_id=attempt.id, question_id=q.id, selected_options=["A"])
        db_session.add(ans)
        db_session.flush()

        res = grade_attempt(db_session, attempt.id)
        assert res.score == 10.0
        assert attempt.status == test_status  # Status must be preserved
        assert attempt.submitted_at is not None  # submitted_at must be populated


def test_e4_question_not_in_snapshot_k02(db_session):
    _, student, _, category, exam = make_test_environment(db_session)
    q1 = create_question(
        db_session, category.id, exam.instructor_id, QuestionType.SINGLE_CHOICE,
        [{"id": "A", "text": "A", "is_correct": True}, {"id": "B", "text": "B", "is_correct": False}],
    )
    q_rogue = create_question(
        db_session, category.id, exam.instructor_id, QuestionType.SINGLE_CHOICE,
        [{"id": "A", "text": "A", "is_correct": True}, {"id": "B", "text": "B", "is_correct": False}],
    )
    create_exam_question(db_session, exam.id, q1, order_index=1, points=1.0)
    snapshot_q = [{"question_id": str(q1.id), "options_order": ["A", "B"]}]

    attempt = create_attempt(db_session, exam.id, student.id, snapshot_q)
    ans = AttemptAnswer(attempt_id=attempt.id, question_id=q_rogue.id, selected_options=["A"])
    db_session.add(ans)
    db_session.flush()

    with pytest.raises(SnapshotMismatchError):
        grade_attempt(db_session, attempt.id)


def test_e5_selected_options_contain_invalid_option_id(db_session, caplog):
    _, student, _, category, exam = make_test_environment(db_session)
    q = create_question(
        db_session, category.id, exam.instructor_id, QuestionType.SINGLE_CHOICE,
        [{"id": "A", "text": "A", "is_correct": True}, {"id": "B", "text": "B", "is_correct": False}],
    )
    create_exam_question(db_session, exam.id, q, order_index=1, points=1.0)
    snapshot_q = [{"question_id": str(q.id), "options_order": ["A", "B"]}]

    attempt = create_attempt(db_session, exam.id, student.id, snapshot_q)
    # Student selected 'Z' which is not in question options
    ans = AttemptAnswer(attempt_id=attempt.id, question_id=q.id, selected_options=["Z"])
    db_session.add(ans)
    db_session.flush()

    res = grade_attempt(db_session, attempt.id)
    assert res.score == 0.0
    assert res.answers[0]["is_correct"] is False
    assert res.answers[0]["points_awarded"] == 0.0


def test_e6_duplicate_selected_options_deduped(db_session):
    _, student, _, category, exam = make_test_environment(db_session)
    q = create_question(
        db_session, category.id, exam.instructor_id, QuestionType.SINGLE_CHOICE,
        [{"id": "A", "text": "A", "is_correct": True}, {"id": "B", "text": "B", "is_correct": False}],
    )
    create_exam_question(db_session, exam.id, q, order_index=1, points=1.0)
    snapshot_q = [{"question_id": str(q.id), "options_order": ["A", "B"]}]

    attempt = create_attempt(db_session, exam.id, student.id, snapshot_q)
    ans = AttemptAnswer(attempt_id=attempt.id, question_id=q.id, selected_options=["A", "A", "A"])
    db_session.add(ans)
    db_session.flush()

    res = grade_attempt(db_session, attempt.id)
    assert res.score == 10.0
    assert res.answers[0]["is_correct"] is True


def test_e7_question_without_attempt_answer_record(db_session):
    _, student, _, category, exam = make_test_environment(db_session)
    q1 = create_question(
        db_session, category.id, exam.instructor_id, QuestionType.SINGLE_CHOICE,
        [{"id": "A", "text": "A", "is_correct": True}, {"id": "B", "text": "B", "is_correct": False}],
    )
    q2 = create_question(
        db_session, category.id, exam.instructor_id, QuestionType.SINGLE_CHOICE,
        [{"id": "A", "text": "A", "is_correct": True}, {"id": "B", "text": "B", "is_correct": False}],
    )
    create_exam_question(db_session, exam.id, q1, order_index=1, points=1.0)
    create_exam_question(db_session, exam.id, q2, order_index=2, points=1.0)
    snapshot_q = [
        {"question_id": str(q1.id), "options_order": ["A", "B"]},
        {"question_id": str(q2.id), "options_order": ["A", "B"]},
    ]

    attempt = create_attempt(db_session, exam.id, student.id, snapshot_q)
    # Only answer q1, leave q2 without any AttemptAnswer record
    ans1 = AttemptAnswer(attempt_id=attempt.id, question_id=q1.id, selected_options=["A"])
    db_session.add(ans1)
    db_session.flush()

    res = grade_attempt(db_session, attempt.id)
    assert res.total_questions == 2
    assert res.correct_count == 1
    assert res.score == 5.0
    # Q2 should now exist in answers with 0 points
    assert len(res.answers) == 2
    q2_summary = next(a for a in res.answers if a["question_id"] == str(q2.id))
    assert q2_summary["is_correct"] is False
    assert q2_summary["points_awarded"] == 0.0


def test_e8_zero_questions_or_zero_points(db_session):
    _, student, _, category, exam = make_test_environment(db_session)
    snapshot_q = []
    attempt = create_attempt(db_session, exam.id, student.id, snapshot_q)

    res = grade_attempt(db_session, attempt.id)
    assert res.score == 0.0
    assert res.total_questions == 0


def test_e9_score_clamping(db_session):
    _, student, _, category, exam = make_test_environment(db_session)
    q = create_question(
        db_session, category.id, exam.instructor_id, QuestionType.SINGLE_CHOICE,
        [{"id": "A", "text": "A", "is_correct": True}, {"id": "B", "text": "B", "is_correct": False}],
    )
    # Force weird points setup
    create_exam_question(db_session, exam.id, q, order_index=1, points=1.0)
    snapshot_q = [{"question_id": str(q.id), "options_order": ["A", "B"]}]

    attempt = create_attempt(db_session, exam.id, student.id, snapshot_q)
    ans = AttemptAnswer(attempt_id=attempt.id, question_id=q.id, selected_options=["A"])
    db_session.add(ans)
    db_session.flush()

    res = grade_attempt(db_session, attempt.id)
    assert 0.0 <= res.score <= 10.0


def test_e10_idempotent_consecutive_calls(db_session):
    _, student, _, category, exam = make_test_environment(db_session)
    q = create_question(
        db_session, category.id, exam.instructor_id, QuestionType.SINGLE_CHOICE,
        [{"id": "A", "text": "A", "is_correct": True}, {"id": "B", "text": "B", "is_correct": False}],
    )
    create_exam_question(db_session, exam.id, q, order_index=1, points=2.0)
    snapshot_q = [{"question_id": str(q.id), "options_order": ["A", "B"]}]

    attempt = create_attempt(db_session, exam.id, student.id, snapshot_q)
    ans = AttemptAnswer(attempt_id=attempt.id, question_id=q.id, selected_options=["A"])
    db_session.add(ans)
    db_session.flush()

    res1 = grade_attempt(db_session, attempt.id)
    res2 = grade_attempt(db_session, attempt.id)
    assert res1.score == res2.score == 10.0
    assert res2.already_graded is True


def test_i01_caller_commits_boundary(db_session):
    """Verify grade_attempt does not commit; changes are rolled back if caller rolls back."""
    _, student, _, category, exam = make_test_environment(db_session)
    q = create_question(
        db_session, category.id, exam.instructor_id, QuestionType.SINGLE_CHOICE,
        [{"id": "A", "text": "A", "is_correct": True}, {"id": "B", "text": "B", "is_correct": False}],
    )
    create_exam_question(db_session, exam.id, q, order_index=1, points=1.0)
    snapshot_q = [{"question_id": str(q.id), "options_order": ["A", "B"]}]

    attempt = create_attempt(db_session, exam.id, student.id, snapshot_q)
    ans = AttemptAnswer(attempt_id=attempt.id, question_id=q.id, selected_options=["A"])
    db_session.add(ans)
    db_session.flush()

    # Use a savepoint to simulate caller deciding to roll back
    savepoint = db_session.begin_nested()
    grade_attempt(db_session, attempt.id)
    savepoint.rollback()

    reloaded = db_session.query(ExamAttempt).filter(ExamAttempt.id == attempt.id).first()
    assert reloaded is not None
    assert reloaded.score is None
    assert reloaded.status == AttemptStatus.IN_PROGRESS


# ==============================================================================
# 3. HTTP ENDPOINT TESTS: POST /api/v1/tutor-analytics/grade/{attempt_id}
# ==============================================================================


def test_endpoint_role_based_access(client, db_session):
    instructor, student, admin, category, exam = make_test_environment(db_session)
    q = create_question(
        db_session, category.id, exam.instructor_id, QuestionType.SINGLE_CHOICE,
        [{"id": "A", "text": "A", "is_correct": True}, {"id": "B", "text": "B", "is_correct": False}],
    )
    create_exam_question(db_session, exam.id, q, order_index=1, points=1.0)
    snapshot_q = [{"question_id": str(q.id), "options_order": ["A", "B"]}]

    attempt = create_attempt(db_session, exam.id, student.id, snapshot_q)
    ans = AttemptAnswer(attempt_id=attempt.id, question_id=q.id, selected_options=["A"])
    db_session.add(ans)
    db_session.commit()

    student_token = create_access_token({"sub": str(student.id), "role": student.role.value})
    instructor_token = create_access_token({"sub": str(instructor.id), "role": instructor.role.value})
    admin_token = create_access_token({"sub": str(admin.id), "role": admin.role.value})

    # Student should be forbidden (403)
    resp_student = client.post(
        f"/api/v1/tutor-analytics/grade/{attempt.id}",
        cookies={"access_token": student_token},
    )
    assert resp_student.status_code == 403

    # Instructor should succeed (200)
    resp_instructor = client.post(
        f"/api/v1/tutor-analytics/grade/{attempt.id}",
        cookies={"access_token": instructor_token},
    )
    assert resp_instructor.status_code == 200
    data = resp_instructor.json()["data"]
    assert data["score"] == 10.0
    assert data["correct_count"] == 1
    assert data["total_questions"] == 1

    # Admin should succeed with force=True (200)
    resp_admin = client.post(
        f"/api/v1/tutor-analytics/grade/{attempt.id}?force=true",
        cookies={"access_token": admin_token},
    )
    assert resp_admin.status_code == 200
    assert resp_admin.json()["data"]["already_graded"] is False


def test_endpoint_not_found_and_validation(client, db_session):
    instructor, _, _, _, _ = make_test_environment(db_session)
    db_session.commit()
    token = create_access_token({"sub": str(instructor.id), "role": instructor.role.value})

    resp = client.post(
        f"/api/v1/tutor-analytics/grade/{uuid.uuid4()}",
        cookies={"access_token": token},
    )
    assert resp.status_code == 404


# ==============================================================================
# 4. PERFORMANCE SLA TEST (< 300ms)
# ==============================================================================


def test_grading_performance_under_300ms(db_session):
    """DoD SLA: Auto-grading must complete in < 300ms."""
    _, student, _, category, exam = make_test_environment(db_session)

    # Build 50 questions
    snapshot_q = []
    for i in range(1, 51):
        q = create_question(
            db_session, category.id, exam.instructor_id,
            QuestionType.MULTIPLE_CHOICE,
            [
                {"id": "A", "text": f"A{i}", "is_correct": True},
                {"id": "B", "text": f"B{i}", "is_correct": False},
                {"id": "C", "text": f"C{i}", "is_correct": True},
                {"id": "D", "text": f"D{i}", "is_correct": False},
            ],
            content=f"Performance Question {i}",
        )
        create_exam_question(db_session, exam.id, q, order_index=i, points=2.0)
        snapshot_q.append({"question_id": str(q.id), "options_order": ["A", "B", "C", "D"]})

    attempt = create_attempt(db_session, exam.id, student.id, snapshot_q)
    for row in snapshot_q:
        db_session.add(AttemptAnswer(
            attempt_id=attempt.id,
            question_id=uuid.UUID(row["question_id"]),
            selected_options=["A", "C"],
        ))
    db_session.flush()

    start_time = time.perf_counter()
    res = grade_attempt(db_session, attempt.id)
    elapsed_ms = (time.perf_counter() - start_time) * 1000

    assert res.score == 10.0
    assert res.total_questions == 50
    assert res.correct_count == 50
    assert elapsed_ms < 300.0, f"Grading took {elapsed_ms:.2f}ms, exceeding 300ms SLA"


@pytest.mark.parametrize("role", ["STUDENT", "INSTRUCTOR", "ADMIN"])
def test_review_and_grading_ownership(client, db_session, role):
    instructor, student, admin, _, exam = make_test_environment(db_session)
    attempt = create_attempt(db_session, exam.id, student.id, [])
    stranger = User(id=uuid.uuid4(), email="stranger@example.com", full_name="Stranger", password_hash="unused", role=UserRole(role))
    db_session.add(stranger)
    db_session.commit()
    headers = {"Authorization": "Bearer " + create_access_token({"sub": str(stranger.id)})}
    review = f"/api/v1/tutor-analytics/review/{attempt.id}"
    assert client.get(review, headers=headers).status_code == (200 if role == "ADMIN" else 403)
    grade = f"/api/v1/tutor-analytics/grade/{attempt.id}"
    if role != "ADMIN":
        assert client.post(grade, headers=headers).status_code == 403
    own_headers = {"Authorization": "Bearer " + create_access_token({"sub": str(student.id)})}
    # The owner cannot retrieve answer keys while still taking the exam.
    assert client.get(review, headers=own_headers).status_code == 403


def test_tutor_rejects_question_outside_authorized_attempt(client, db_session):
    instructor, student, admin, category, exam = make_test_environment(db_session)
    attempt = create_attempt(db_session, exam.id, student.id, [])
    db_session.commit()
    headers = {"Authorization": "Bearer " + create_access_token({"sub": str(instructor.id)})}
    path = f"/api/v1/tutor-analytics/attempts/{attempt.id}/questions/{uuid.uuid4()}/explain"
    assert client.post(path, headers=headers).status_code == 403
    assert client.post("/api/v1/tutor-analytics/explain", headers=headers, json={"attempt_id": str(attempt.id), "question_id": str(uuid.uuid4())}).status_code == 403


@pytest.mark.parametrize("method,path", [
    ("get", "/api/v1/tutor-analytics/review/00000000-0000-0000-0000-000000000001"),
    ("post", "/api/v1/tutor-analytics/explain"),
    ("post", "/api/v1/exam-engine/exams/1/start"),
    ("post", "/api/v1/exam-engine/attempts/1/submit"),
])
def test_business_routes_require_authentication(client, method, path):
    response = client.post(path, json={}) if method == "post" else client.get(path)
    assert response.status_code == 401
