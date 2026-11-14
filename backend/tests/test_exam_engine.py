"""#12 HTTP integration: real PostgreSQL when AUTH_TEST_DATABASE_URL is set."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.core.security import create_access_token, verify_password
from app.models.entities import Exam, ExamAttempt, ExamQuestion, AttemptAnswer, AttemptStatus, User, UserRole, QuestionType
from app.modules.exam_engine import service
from app.modules.exam_engine.schemas import SubmitInput
from test_grading import grading_db_engine, db_session, client, make_test_environment, create_question

PREFIX = "/api/v1/exam-engine"


def headers(user):
    return {"Authorization": "Bearer " + create_access_token({"sub": str(user.id)})}


@pytest.fixture
def room(client, db_session):
    instructor, student, admin, category, unused = make_test_environment(db_session)
    question = create_question(db_session, category.id, instructor.id, QuestionType.SINGLE_CHOICE,
        [{"id": "A", "text": "Correct", "is_correct": True}, {"id": "B", "text": "Wrong", "is_correct": False}])
    db_session.commit()
    timestamp = datetime.now(timezone.utc)
    payload = {"title": "Integration exam", "duration_minutes": 30, "pin": "123456", "max_attempts": 2,
        "start_time": (timestamp-timedelta(minutes=1)).isoformat(), "end_time": (timestamp+timedelta(hours=1)).isoformat(),
        "is_published": True, "questions": [{"question_id": str(question.id), "points": 2}]}
    response = client.post(PREFIX+"/exams", json=payload, headers=headers(instructor))
    assert response.status_code == 201, response.text
    exam = response.json()["data"]
    return instructor, student, admin, question, payload, exam


def enter(client, student, exam, pin="123456"):
    return client.post(PREFIX+"/exams/join", json={"exam_code": exam["exam_code"], "pin": pin}, headers=headers(student))


def start(client, student, exam):
    return client.post(PREFIX+f'/exams/{exam["id"]}/start', headers=headers(student))


def test_create_pin_and_atomic_validation(client, db_session, room):
    instructor, student, admin, question, payload, exam = room
    stored = db_session.get(Exam, UUID(exam["id"]))
    assert len(exam["exam_code"]) == 8
    assert verify_password("123456", stored.access_password_hash)
    assert "access_password_hash" not in exam and "pin" not in exam
    assert db_session.query(ExamQuestion).filter_by(exam_id=stored.id).count() == 1
    count = db_session.query(Exam).count()
    bad = {**payload, "questions": [{"question_id": str(uuid4())}]}
    assert client.post(PREFIX+"/exams", json=bad, headers=headers(instructor)).status_code == 400
    assert db_session.query(Exam).count() == count
    assert client.post(PREFIX+"/exams", json=payload, headers=headers(student)).status_code == 403
    assert client.post(PREFIX+"/exams", json=payload).status_code == 401
    assert client.post(PREFIX+"/exams", json=payload, headers={**headers(instructor), "Origin": "https://unapproved.invalid"}).status_code == 403


@pytest.mark.parametrize("change", [
    {"duration_minutes": 0}, {"max_attempts": 0}, {"title": "   "},
    {"end_time": "2000-01-01T00:00:00Z"}, {"start_time": "2026-11-09T10:00:00"},
    {"pin": "é"*40}, {"questions": []},
])
def test_invalid_configuration(client, room, change):
    instructor, _, _, _, payload, _ = room
    assert client.post(PREFIX+"/exams", json={**payload, **change}, headers=headers(instructor)).status_code == 422


def test_join_grant_and_resume(client, db_session, room):
    _, student, _, _, _, exam = room
    assert start(client, student, exam).status_code == 403
    assert enter(client, student, exam, "wrong").status_code == 403
    assert db_session.query(ExamAttempt).count() == 0
    response = enter(client, student, exam)
    assert response.status_code == 200
    assert "HttpOnly" in response.headers["set-cookie"]
    assert db_session.query(ExamAttempt).count() == 0
    assert client.get(PREFIX+f'/exams/{exam["id"]}/lobby', headers=headers(student)).status_code == 200
    first = start(client, student, exam)
    assert first.status_code == 200, first.text
    assert "is_correct" not in first.text and "explanation" not in first.text
    second = start(client, student, exam).json()["data"]
    assert second == first.json()["data"]
    assert db_session.query(ExamAttempt).count() == 1


def test_submit_grade_review_and_freeze(client, db_session, room):
    instructor, student, admin, question, payload, exam = room
    enter(client, student, exam)
    attempt = start(client, student, exam).json()["data"]
    path = PREFIX+f'/attempts/{attempt["attempt_id"]}/submit'
    bad = {"answers": [{"question_id": str(uuid4()), "selected_options": ["A"]}]}
    assert client.post(path, json=bad, headers=headers(student)).status_code == 400
    assert db_session.query(AttemptAnswer).count() == 0
    assert client.post(path, json={"answers": []}, headers=headers(admin)).status_code == 403
    assert client.put(PREFIX+f'/exams/{exam["id"]}', json=payload, headers=headers(instructor)).status_code == 409
    assert client.patch(f'/api/v1/ai-generator/question-bank/questions/{question.id}', json={"content": "Changed"}, headers=headers(instructor)).status_code == 409
    response = client.post(path, json={"answers": [{"question_id": str(question.id), "selected_options": ["A"]}]}, headers=headers(student))
    assert response.status_code == 200, response.text
    assert response.json()["data"]["score"] == 10
    assert response.json()["data"]["status"] == "SUBMITTED"
    assert client.post(path, json={"answers": []}, headers=headers(student)).status_code == 409
    assert client.get(f'/api/v1/tutor-analytics/review/{attempt["attempt_id"]}', headers=headers(student)).status_code == 200


def test_grading_failure_rolls_back_answers(client, db_session, room, monkeypatch):
    _, student, _, question, _, exam = room
    enter(client, student, exam)
    attempt = start(client, student, exam).json()["data"]
    def fail(*args):
        raise RuntimeError("grading unavailable")
    monkeypatch.setattr(service, "grade_attempt", fail)
    with pytest.raises(RuntimeError, match="grading unavailable"):
        client.post(PREFIX+f'/attempts/{attempt["attempt_id"]}/submit', headers=headers(student),
            json={"answers": [{"question_id": str(question.id), "selected_options": ["A"]}]})
    assert db_session.query(AttemptAnswer).count() == 0
    assert db_session.get(ExamAttempt, UUID(attempt["attempt_id"])).status == AttemptStatus.IN_PROGRESS


def test_expiry_limits_and_time_window(client, db_session, room, monkeypatch):
    instructor, student, _, question, payload, exam = room
    enter(client, student, exam)
    original = service.now()
    monkeypatch.setattr(service, "now", lambda: original - timedelta(hours=1))
    assert start(client, student, exam).status_code == 403
    monkeypatch.setattr(service, "now", lambda: original)
    first = start(client, student, exam).json()["data"]
    monkeypatch.setattr(service, "now", lambda: original + timedelta(minutes=31))
    second = start(client, student, exam).json()["data"]
    assert first["attempt_id"] != second["attempt_id"]
    assert db_session.get(ExamAttempt, UUID(first["attempt_id"])).status == AttemptStatus.EXPIRED
    # End time is authoritative even if duration would allow longer.
    assert service.aware(db_session.get(ExamAttempt, UUID(second["attempt_id"])).expires_at) <= datetime.fromisoformat(exam["end_time"])
    monkeypatch.setattr(service, "now", lambda: original + timedelta(hours=2))
    assert start(client, student, exam).status_code == 403
    response = client.post(PREFIX+f'/attempts/{second["attempt_id"]}/submit', headers=headers(student), json={"answers": []})
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "EXPIRED"


def test_recovery_saved_answers_and_expiry_cutoff(client, db_session, room, monkeypatch):
    _, student, _, question, _, exam = room
    enter(client, student, exam)
    attempt = start(client, student, exam).json()["data"]
    path = PREFIX + f'/attempts/{attempt["attempt_id"]}'
    answer = {"answers": [{"question_id": str(question.id), "selected_options": ["A"]}]}
    assert client.post(path + "/answers", headers=headers(student), json=answer).status_code == 200
    recovered = client.get(path, headers=headers(student))
    assert recovered.status_code == 200
    assert datetime.fromisoformat(recovered.json()["data"]["server_now"]).tzinfo is not None
    assert recovered.json()["data"]["answers"] == {str(question.id): ["A"]}
    assert "is_correct" not in recovered.text
    stranger = User(email="recovery-other@example.com", full_name="Other", role=UserRole.STUDENT, password_hash="unused")
    db_session.add(stranger); db_session.commit()
    assert client.get(path, headers=headers(stranger)).status_code == 403
    assert client.post(path + "/answers", headers=headers(stranger), json=answer).status_code == 403
    monkeypatch.setattr(service, "now", lambda: datetime.fromisoformat(attempt["expires_at"]) + timedelta(seconds=1))
    wrong = {"answers": [{"question_id": str(question.id), "selected_options": ["B"]}]}
    assert client.post(path + "/answers", headers=headers(student), json=wrong).status_code == 409
    result = client.post(path + "/submit", headers=headers(student), json=wrong)
    assert result.status_code == 200
    assert result.json()["data"]["score"] == 10
    assert result.json()["data"]["status"] == "EXPIRED"


def test_wrong_owner_and_grant_user_binding(client, db_session, room):
    instructor, student, admin, _, payload, exam = room
    other = User(email="other-exam@example.com", full_name="Other", role=UserRole.INSTRUCTOR, password_hash="unused")
    stranger = User(email="other-student@example.com", full_name="Other", role=UserRole.STUDENT, password_hash="unused")
    db_session.add_all([other, stranger]); db_session.commit()
    assert client.post(PREFIX+"/exams", json=payload, headers=headers(other)).status_code == 403
    assert client.get(PREFIX+f'/exams/{exam["id"]}', headers=headers(other)).status_code == 403
    assert all(item["id"] != exam["id"] for item in client.get(PREFIX+"/exams", headers=headers(other)).json()["data"])
    enter(client, student, exam)
    assert start(client, stranger, exam).status_code == 403
    attempt = start(client, student, exam).json()["data"]
    assert client.post(PREFIX+f'/attempts/{attempt["attempt_id"]}/submit', headers=headers(stranger), json={"answers": []}).status_code == 403


def test_edit_invalidates_entry_and_publishing(client, db_session, room):
    instructor, student, _, _, payload, exam = room
    enter(client, student, exam)
    changed = {**payload, "pin": "new-pin", "is_published": False}
    assert client.put(PREFIX+f'/exams/{exam["id"]}', json=changed, headers=headers(instructor)).status_code == 200
    assert start(client, student, exam).status_code == 403
    assert enter(client, student, exam, "new-pin").status_code == 403


def test_attempt_limit_and_empty_submission(client, db_session, room):
    instructor, student, _, _, payload, exam = room
    payload["max_attempts"] = 1
    assert client.put(PREFIX+f'/exams/{exam["id"]}', json=payload, headers=headers(instructor)).status_code == 200
    enter(client, student, exam)
    attempt = start(client, student, exam).json()["data"]
    response = client.post(PREFIX+f'/attempts/{attempt["attempt_id"]}/submit', headers=headers(student), json={"answers": []})
    assert response.status_code == 200
    assert response.json()["data"]["score"] == 0
    assert start(client, student, exam).status_code == 403


@pytest.mark.parametrize("options", [["Z"], ["A", "A"]])
def test_reject_invalid_option_ids(client, db_session, room, options):
    _, student, _, question, _, exam = room
    enter(client, student, exam)
    attempt = start(client, student, exam).json()["data"]
    response = client.post(PREFIX+f'/attempts/{attempt["attempt_id"]}/submit', headers=headers(student),
        json={"answers": [{"question_id": str(question.id), "selected_options": options}]})
    assert response.status_code == 400
    assert db_session.query(AttemptAnswer).count() == 0


def test_optional_pin_and_code_collision_retry(client, db_session, room, monkeypatch):
    instructor, student, _, _, payload, exam = room
    payload["pin"] = None
    monkeypatch.setattr(service.secrets, "choice", lambda alphabet: "X")
    first = client.post(PREFIX+"/exams", json=payload, headers=headers(instructor))
    assert first.status_code == 201
    assert not first.json()["data"]["requires_pin"]
    count = db_session.query(Exam).count()
    assert client.post(PREFIX+"/exams", json=payload, headers=headers(instructor)).status_code == 409
    assert db_session.query(Exam).count() == count
    assert enter(client, student, first.json()["data"], "").status_code == 200


def test_concurrent_start_postgres(auth_engine):
    if auth_engine.dialect.name != "postgresql":
        pytest.skip("PostgreSQL is required to exercise row locking")
    # Separate committed setup permits genuinely independent connections.
    suffix = uuid4().hex
    with Session(auth_engine) as db:
        instructor = User(email=f"i-{suffix}@example.com", full_name="I", password_hash="unused", role=UserRole.INSTRUCTOR)
        student = User(email=f"s-{suffix}@example.com", full_name="S", password_hash="unused", role=UserRole.STUDENT)
        db.add_all([instructor, student]); db.flush()
        from app.models.entities import Category, CognitiveLevel, Question
        category = Category(name=suffix, created_by=instructor.id); db.add(category); db.flush()
        q = Question(category_id=category.id, creator_id=instructor.id, content="Concurrent", question_type=QuestionType.SINGLE_CHOICE,
            cognitive_level=CognitiveLevel.REMEMBER, options=[{"id":"A","text":"A","is_correct":True},{"id":"B","text":"B","is_correct":False}])
        db.add(q); db.flush()
        timestamp = service.now()
        exam = Exam(title="Concurrent", exam_code=suffix[:12], instructor_id=instructor.id, duration_minutes=5, max_attempts=1,
            start_time=timestamp-timedelta(minutes=1), end_time=timestamp+timedelta(hours=1), is_published=True)
        db.add(exam); db.flush()
        db.add(ExamQuestion(exam_id=exam.id, question_id=q.id, order_index=1))
        db.commit()
        ids = (instructor.id, student.id, category.id, q.id, exam.id)
    try:
        def run(_):
            with Session(auth_engine) as db:
                user = db.get(User, ids[1])
                return service.start_attempt(db, ids[4], user)["attempt_id"]
        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(run, range(2)))
        assert results[0] == results[1]
        with Session(auth_engine) as db:
            assert db.query(ExamAttempt).filter_by(exam_id=ids[4]).count() == 1
        def submit_once(_):
            with Session(auth_engine) as db:
                try:
                    result = service.submit_attempt(db, results[0], db.get(User, ids[1]),
                        SubmitInput(answers=[{"question_id": ids[3], "selected_options": ["A"]}]))
                    return result["score"]
                except HTTPException as error:
                    db.rollback()
                    return error.status_code
        with ThreadPoolExecutor(max_workers=2) as executor:
            scores = list(executor.map(submit_once, range(2)))
        assert sorted(scores) == [10.0, 409]
    finally:
        with Session(auth_engine) as db:
            attempt_ids = db.query(ExamAttempt.id).filter_by(exam_id=ids[4]).all()
            if attempt_ids:
                db.query(AttemptAnswer).filter(AttemptAnswer.attempt_id.in_([r[0] for r in attempt_ids])).delete(synchronize_session=False)
            db.query(ExamAttempt).filter_by(exam_id=ids[4]).delete()
            db.query(ExamQuestion).filter_by(exam_id=ids[4]).delete()
            db.query(Exam).filter_by(id=ids[4]).delete()
            db.query(Question).filter_by(id=ids[3]).delete()
            db.query(Category).filter_by(id=ids[2]).delete()
            db.query(User).filter(User.id.in_(ids[:2])).delete(synchronize_session=False)
            db.commit()
