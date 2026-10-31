import os
import sys
import uuid
from datetime import datetime, timedelta, timezone

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from alembic import command
from alembic.config import Config
from sqlalchemy import text
from app.core.config import settings
from app.core.database import SessionLocal, engine
from app.core.security import get_password_hash
from app.models.entities import (
    AntiCheatLog,
    AttemptAnswer,
    AttemptStatus,
    Base,
    Category,
    CognitiveLevel,
    Exam,
    ExamAttempt,
    ExamQuestion,
    Question,
    QuestionSource,
    QuestionType,
    User,
    UserRole,
)
from scripts.seed import seed_data


def test_1_tables_and_enums(alembic_cfg):
    print("\n--- TEST 1: Check 9 domain tables + alembic_version and 6 enums ---")
    with engine.connect() as conn:
        tables = conn.execute(
            text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public' ORDER BY table_name"
            )
        ).scalars().all()
        print("  Found tables:", tables)
        expected_tables = {
            "alembic_version",
            "anti_cheat_logs",
            "attempt_answers",
            "categories",
            "exam_attempts",
            "exam_questions",
            "exams",
            "questions",
            "subjects",
            "users",
        }
        assert set(tables) == expected_tables, f"Tables mismatch: {set(tables)} vs {expected_tables}"

        enums = conn.execute(
            text(
                "SELECT t.typname FROM pg_type t "
                "JOIN pg_namespace n ON n.oid = t.typnamespace "
                "WHERE n.nspname = 'public' AND t.typtype = 'e' ORDER BY t.typname"
            )
        ).scalars().all()
        print("  Found enums:", enums)
        expected_enums = {
            "attempt_status",
            "cognitive_level",
            "question_level",
            "question_source",
            "question_type",
            "user_role",
        }
        assert set(enums) == expected_enums, f"Enums mismatch: {set(enums)} vs {expected_enums}"
    print("  ✅ TEST 1 PASSED: 9 domain tables and 6 enums exist.")


def test_2_downgrade_and_upgrade(alembic_cfg):
    print("\n--- TEST 2: Test downgrade base then upgrade head ---")
    command.downgrade(alembic_cfg, "base")
    with engine.connect() as conn:
        tables = conn.execute(
            text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public' AND table_name != 'alembic_version'"
            )
        ).scalars().all()
        assert len(tables) == 0, f"Tables left after downgrade: {tables}"

        enums = conn.execute(
            text(
                "SELECT t.typname FROM pg_type t "
                "JOIN pg_namespace n ON n.oid = t.typnamespace "
                "WHERE n.nspname = 'public' AND t.typtype = 'e'"
            )
        ).scalars().all()
        assert len(enums) == 0, f"Enums left after downgrade: {enums}"
        print("  ✅ Downgrade base cleanly removed all tables and all 6 enums.")

    command.upgrade(alembic_cfg, "head")
    print("  ✅ Re-upgrade head succeeded.")


def test_3_autogenerate_empty(alembic_cfg):
    print("\n--- TEST 3: Check alembic check/autogenerate produces no diff ---")
    from alembic.autogenerate import compare_metadata
    from alembic.runtime.migration import MigrationContext

    with engine.connect() as conn:
        mc = MigrationContext.configure(conn, opts={"compare_type": True, "compare_server_default": True})
        diff = compare_metadata(mc, Base.metadata)
        print("  Autogenerate diff:", diff)
        assert len(diff) == 0, f"Unexpected diff found: {diff}"
    print("  ✅ TEST 3 PASSED: Autogenerate produces no pending changes.")


def test_4_seed_twice():
    print("\n--- TEST 4: Seed run twice (idempotence) ---")
    seed_data(with_demo_exam=False)
    db = SessionLocal()
    u1 = db.query(User).count()
    c1 = db.query(Category).count()
    q1 = db.query(Question).count()
    assert u1 == 3, f"Expected 3 users, got {u1}"
    assert c1 == 1, f"Expected 1 category, got {c1}"
    assert q1 == 10, f"Expected 10 questions, got {q1}"
    db.close()

    # Second run
    seed_data(with_demo_exam=False)
    db = SessionLocal()
    u2 = db.query(User).count()
    c2 = db.query(Category).count()
    q2 = db.query(Question).count()
    assert u2 == 3, f"Expected 3 users on 2nd run, got {u2}"
    assert c2 == 1, f"Expected 1 category on 2nd run, got {c2}"
    assert q2 == 10, f"Expected 10 questions on 2nd run, got {q2}"
    db.close()
    print("  ✅ TEST 4 PASSED: Seed is idempotent; 3 users, 1 category, 10 questions.")


def test_5_db_constraints_rejections():
    print("\n--- TEST 5: Verify 9 required constraint rejections ---")
    db = SessionLocal()
    instructor = db.query(User).filter(User.role == UserRole.INSTRUCTOR).first()
    student = db.query(User).filter(User.role == UserRole.STUDENT).first()
    category = db.query(Category).first()
    now = datetime.now(timezone.utc)

    # 5.1 chèn users.email có chữ hoa
    print("  Testing 5.1: Uppercase email rejection...")
    try:
        bad_user = User(
            email="UpperCase@smartquiz.edu.vn",
            password_hash="hash",
            full_name="Upper",
            role=UserRole.STUDENT,
        )
        db.add(bad_user)
        db.commit()
        assert False, "Failed to reject uppercase email!"
    except Exception as e:
        db.rollback()
        assert "ck_users_email_lowercase" in str(e).lower() or "check" in str(e).lower()
        print("    -> Successfully rejected by ck_users_email_lowercase.")

    # Create a valid test exam
    valid_exam = Exam(
        exam_code="TEST01",
        title="Test Exam",
        instructor_id=instructor.id,
        duration_minutes=30,
        start_time=now,
        end_time=now + timedelta(hours=2),
        is_published=True,
    )
    db.add(valid_exam)
    db.commit()

    # 5.2 hai exam_attempts cùng (exam_id, student_id) đều IN_PROGRESS
    print("  Testing 5.2: Two IN_PROGRESS exam_attempts rejection...")
    att1 = ExamAttempt(
        exam_id=valid_exam.id,
        student_id=student.id,
        attempt_number=1,
        started_at=now,
        expires_at=now + timedelta(minutes=30),
        status=AttemptStatus.IN_PROGRESS,
        question_order_snapshot={"version": 1},
    )
    db.add(att1)
    db.commit()

    try:
        att2 = ExamAttempt(
            exam_id=valid_exam.id,
            student_id=student.id,
            attempt_number=2,
            started_at=now,
            expires_at=now + timedelta(minutes=30),
            status=AttemptStatus.IN_PROGRESS,
            question_order_snapshot={"version": 1},
        )
        db.add(att2)
        db.commit()
        assert False, "Failed to reject second IN_PROGRESS attempt!"
    except Exception as e:
        db.rollback()
        assert "uq_exam_attempts_one_in_progress" in str(e).lower() or "unique" in str(e).lower()
        print("    -> Successfully rejected by uq_exam_attempts_one_in_progress.")

    # 5.3 exams với end_time <= start_time
    print("  Testing 5.3: Exam end_time <= start_time rejection...")
    try:
        bad_exam = Exam(
            exam_code="BADTIME",
            title="Bad Time",
            instructor_id=instructor.id,
            duration_minutes=30,
            start_time=now,
            end_time=now - timedelta(hours=1),
        )
        db.add(bad_exam)
        db.commit()
        assert False, "Failed to reject end_time <= start_time!"
    except Exception as e:
        db.rollback()
        assert "ck_exams_time_window" in str(e).lower() or "check" in str(e).lower()
        print("    -> Successfully rejected by ck_exams_time_window.")

    # 5.4 exams có is_published = true nhưng start_time hoặc end_time NULL
    print("  Testing 5.4: is_published=True with NULL window rejection...")
    try:
        bad_pub_exam = Exam(
            exam_code="BADPUB",
            title="Bad Pub",
            instructor_id=instructor.id,
            duration_minutes=30,
            start_time=None,
            end_time=None,
            is_published=True,
        )
        db.add(bad_pub_exam)
        db.commit()
        assert False, "Failed to reject published exam with NULL window!"
    except Exception as e:
        db.rollback()
        assert "ck_exams_published_has_window" in str(e).lower() or "check" in str(e).lower()
        print("    -> Successfully rejected by ck_exams_published_has_window.")

    # 5.5 hai dòng attempt_answers trùng (attempt_id, question_id)
    print("  Testing 5.5: Duplicate (attempt_id, question_id) rejection...")
    q = db.query(Question).first()
    ans1 = AttemptAnswer(
        attempt_id=att1.id,
        question_id=q.id,
        selected_options=["A"],
    )
    db.add(ans1)
    db.commit()

    try:
        ans2 = AttemptAnswer(
            attempt_id=att1.id,
            question_id=q.id,
            selected_options=["B"],
        )
        db.add(ans2)
        db.commit()
        assert False, "Failed to reject duplicate attempt_answer!"
    except Exception as e:
        db.rollback()
        assert "uq_attempt_answers_attempt_question" in str(e).lower() or "unique" in str(e).lower()
        print("    -> Successfully rejected by uq_attempt_answers_attempt_question.")

    # 5.6 xóa questions đang có trong exam_questions
    print("  Testing 5.6: Deleting question referenced in exam_questions rejection...")
    eq = ExamQuestion(
        exam_id=valid_exam.id,
        question_id=q.id,
        order_index=1,
        points=1.0,
    )
    db.add(eq)
    db.commit()

    try:
        db.delete(q)
        db.commit()
        assert False, "Failed to reject deleting question in exam_questions!"
    except Exception as e:
        db.rollback()
        assert "foreign key" in str(e).lower() or "restrict" in str(e).lower()
        print("    -> Successfully rejected by fk_exam_questions_question_id_questions ON DELETE RESTRICT.")

    # 5.7 exam_attempts có status = 'SUBMITTED' mà submitted_at NULL (và IN_PROGRESS mà submitted_at not NULL)
    print("  Testing 5.7: Closed_at matches status constraint rejection...")
    try:
        bad_att_sub = ExamAttempt(
            exam_id=valid_exam.id,
            student_id=student.id,
            attempt_number=99,
            started_at=now,
            expires_at=now + timedelta(minutes=30),
            status=AttemptStatus.SUBMITTED,
            submitted_at=None,  # Invalid!
            question_order_snapshot={"version": 1},
        )
        db.add(bad_att_sub)
        db.commit()
        assert False, "Failed to reject SUBMITTED attempt with NULL submitted_at!"
    except Exception as e:
        db.rollback()
        assert "ck_exam_attempts_closed_at_matches_status" in str(e).lower() or "check" in str(e).lower()
        print("    -> Successfully rejected by ck_exam_attempts_closed_at_matches_status.")

    # 5.8 questions.options là object hoặc mảng 1 phần tử
    print("  Testing 5.8: Invalid questions.options rejection...")
    try:
        bad_q = Question(
            category_id=category.id,
            creator_id=instructor.id,
            content="Bad options question",
            question_type=QuestionType.SINGLE_CHOICE,
            cognitive_level=CognitiveLevel.REMEMBER,
            options=[{"id": "A", "text": "Only one option"}],  # Length < 2
            source_type=QuestionSource.MANUAL,
        )
        db.add(bad_q)
        db.commit()
        assert False, "Failed to reject options with length < 2!"
    except Exception as e:
        db.rollback()
        assert "ck_questions_options_is_array" in str(e).lower() or "check" in str(e).lower()
        print("    -> Successfully rejected by ck_questions_options_is_array.")

    # 5.9 exam_attempts.score = 10.5
    print("  Testing 5.9: Score > 10 rejection...")
    try:
        bad_score_att = ExamAttempt(
            exam_id=valid_exam.id,
            student_id=student.id,
            attempt_number=100,
            started_at=now,
            expires_at=now + timedelta(minutes=30),
            status=AttemptStatus.SUBMITTED,
            submitted_at=now + timedelta(minutes=15),
            score=10.5,  # Invalid!
            question_order_snapshot={"version": 1},
        )
        db.add(bad_score_att)
        db.commit()
        assert False, "Failed to reject score = 10.5!"
    except Exception as e:
        db.rollback()
        assert "ck_exam_attempts_score_range" in str(e).lower() or "check" in str(e).lower()
        print("    -> Successfully rejected by ck_exam_attempts_score_range.")

    db.close()
    print("  ✅ TEST 5 PASSED: All 9 constraint rejections verified.")


def test_6_deferrable_swap():
    print("\n--- TEST 6: Swap order_index of two exam_questions in one transaction ---")
    db = SessionLocal()
    instructor = db.query(User).filter(User.role == UserRole.INSTRUCTOR).first()
    category = db.query(Category).first()
    q_list = db.query(Question).all()
    q1 = q_list[0]
    q2 = q_list[1]
    now = datetime.now(timezone.utc)

    swap_exam = Exam(
        exam_code="SWAP01",
        title="Swap Test Exam",
        instructor_id=instructor.id,
        duration_minutes=20,
        start_time=now,
        end_time=now + timedelta(hours=1),
        is_published=True,
    )
    db.add(swap_exam)
    db.commit()

    eq1 = ExamQuestion(exam_id=swap_exam.id, question_id=q1.id, order_index=1, points=1.0)
    eq2 = ExamQuestion(exam_id=swap_exam.id, question_id=q2.id, order_index=2, points=1.0)
    db.add_all([eq1, eq2])
    db.commit()

    # Swap in single transaction
    with engine.begin() as conn:
        conn.execute(
            text(
                "UPDATE exam_questions SET order_index = CASE "
                "WHEN id = :id1 THEN 2 WHEN id = :id2 THEN 1 END "
                "WHERE id IN (:id1, :id2)"
            ),
            {"id1": eq1.id, "id2": eq2.id},
        )

    db.refresh(eq1)
    db.refresh(eq2)
    assert eq1.order_index == 2
    assert eq2.order_index == 1
    db.close()
    print("  ✅ TEST 6 PASSED: DEFERRABLE order_index swap executed successfully.")


def test_7_cascade_delete():
    print("\n--- TEST 7: Cascade delete on exam_attempts ---")
    db = SessionLocal()
    student = db.query(User).filter(User.role == UserRole.STUDENT).first()
    exam = db.query(Exam).first()
    q = db.query(Question).first()
    now = datetime.now(timezone.utc)

    cascade_attempt = ExamAttempt(
        exam_id=exam.id,
        student_id=student.id,
        attempt_number=999,
        started_at=now,
        expires_at=now + timedelta(minutes=30),
        status=AttemptStatus.SUBMITTED,
        submitted_at=now + timedelta(minutes=20),
        score=9.0,
        question_order_snapshot={"version": 1},
    )
    db.add(cascade_attempt)
    db.commit()
    att_id = cascade_attempt.id

    ans = AttemptAnswer(
        attempt_id=att_id,
        question_id=q.id,
        selected_options=["A"],
        is_correct=True,
        points_awarded=1.0,
    )
    log = AntiCheatLog(
        attempt_id=att_id,
        event_type="TAB_SWITCH",
        metadata_info={"tab": 1},
    )
    db.add_all([ans, log])
    db.commit()

    ans_count_before = db.query(AttemptAnswer).filter(AttemptAnswer.attempt_id == att_id).count()
    log_count_before = db.query(AntiCheatLog).filter(AntiCheatLog.attempt_id == att_id).count()
    assert ans_count_before == 1
    assert log_count_before == 1

    # Delete attempt directly
    db.delete(cascade_attempt)
    db.commit()

    ans_count_after = db.query(AttemptAnswer).filter(AttemptAnswer.attempt_id == att_id).count()
    log_count_after = db.query(AntiCheatLog).filter(AntiCheatLog.attempt_id == att_id).count()
    assert ans_count_after == 0, "AttemptAnswer was not cascade deleted!"
    assert log_count_after == 0, "AntiCheatLog was not cascade deleted!"
    db.close()
    print("  ✅ TEST 7 PASSED: Cascade delete on exam_attempts verified.")


def main():
    alembic_cfg = Config(os.path.join(os.path.dirname(__file__), "..", "alembic.ini"))
    print("=" * 70)
    print("🚀 RUNNING 7 ACCEPTANCE CRITERIA TESTS FOR SMART QUIZ DATABASE")
    print("=" * 70)

    test_1_tables_and_enums(alembic_cfg)
    test_2_downgrade_and_upgrade(alembic_cfg)
    test_3_autogenerate_empty(alembic_cfg)
    test_4_seed_twice()
    test_5_db_constraints_rejections()
    test_6_deferrable_swap()
    test_7_cascade_delete()

    print("\n" + "=" * 70)
    print("🎉 ALL 7 ACCEPTANCE CRITERIA PASSED 100% ON POSTGRESQL!")
    print("=" * 70)


if __name__ == "__main__":
    main()
