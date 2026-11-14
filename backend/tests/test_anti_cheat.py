from datetime import timedelta
from uuid import UUID, uuid4

import pytest
from app.models.entities import AntiCheatLog, Exam, ExamAttempt, AttemptAnswer, AttemptStatus, User, UserRole
from app.modules.exam_engine import service
from test_exam_engine import room, enter, start, headers, PREFIX
from test_grading import grading_db_engine, db_session, client


def setup_attempt(client, room):
    student, exam = room[1], room[-1]
    enter(client, student, exam)
    attempt = start(client, student, exam).json()["data"]
    return student, attempt, PREFIX + f'/attempts/{attempt["attempt_id"]}/log-violation'


def payload(kind="TAB_SWITCH", **kwargs):
    return {"event_type": kind, "event_id": str(uuid4()), **kwargs}


@pytest.mark.parametrize("kind,count", [("TAB_SWITCH", 1), ("WINDOW_BLUR", 1), ("DEVTOOLS_SHORTCUT", 1), ("COPY_PASTE_ATTEMPT", 0)])
def test_event_policy(client, db_session, room, kind, count):
    student, _, path = setup_attempt(client, room)
    response = client.post(path, headers=headers(student), json=payload(kind, metadata_info={"counted": "forged", "event_id": "forged"}))
    assert response.status_code == 200, response.text
    assert response.json()["data"] == {"status": "IN_PROGRESS", "violation_count": count, "max_tab_violations": 3}
    log = db_session.query(AntiCheatLog).one()
    assert log.event_type == kind
    assert log.metadata_info["counted"] is bool(count)
    assert log.metadata_info["event_id"] != "forged"
    assert response.headers["cache-control"] == "no-store"


def test_dynamic_threshold_answers_grading_and_idempotency(client, db_session, room):
    student, attempt, path = setup_attempt(client, room)
    exam = db_session.get(Exam, UUID(room[-1]["id"]))
    exam.max_tab_violations = 2
    db_session.commit()
    first = payload()
    for _ in range(2):
        assert client.post(path, headers=headers(student), json=first).json()["data"]["violation_count"] == 1
    question = room[3]
    db_session.add(AttemptAnswer(attempt_id=UUID(attempt["attempt_id"]), question_id=question.id, selected_options=["B"]))
    db_session.commit()
    second = payload("DEVTOOLS_SHORTCUT", answers=[{"question_id": str(question.id), "selected_options": ["A"]}])
    response = client.post(path, headers=headers(student), json=second)
    assert response.status_code == 200, response.text
    assert response.json()["data"]["status"] == "LOCKED_VIOLATION"
    db_session.expire_all()
    saved = db_session.get(ExamAttempt, UUID(attempt["attempt_id"]))
    assert saved.violation_count == 2 and saved.submitted_at is not None
    assert float(saved.score) == 10
    assert db_session.query(AttemptAnswer).one().selected_options == ["A"]
    assert client.post(path, headers=headers(student), json=second).json()["data"] == response.json()["data"]
    assert db_session.query(AntiCheatLog).count() == 2


def test_default_threshold_locks_on_third(client, db_session, room):
    student, _, path = setup_attempt(client, room)
    for count in (1, 2, 3):
        response = client.post(path, headers=headers(student), json=payload())
        assert response.status_code == 200
        assert response.json()["data"]["violation_count"] == count
        assert response.json()["data"]["status"] == ("LOCKED_VIOLATION" if count == 3 else "IN_PROGRESS")
    assert db_session.query(AntiCheatLog).count() == 3


def test_lock_creates_answers_and_commits_once(client, db_session, room, monkeypatch):
    student, attempt, path = setup_attempt(client, room)
    db_session.get(Exam, UUID(room[-1]["id"])).max_tab_violations = 1
    db_session.commit()
    commits = []
    original_commit = db_session.commit
    def commit():
        commits.append(True)
        original_commit()
    monkeypatch.setattr(db_session, "commit", commit)
    response = client.post(path, headers=headers(student), json=payload(answers=[{"question_id": str(room[3].id), "selected_options": ["A"]}]))
    assert response.status_code == 200, response.text
    assert response.json()["data"]["status"] == "LOCKED_VIOLATION"
    assert len(commits) == 1
    assert db_session.query(AttemptAnswer).one().selected_options == ["A"]
    assert float(db_session.get(ExamAttempt, UUID(attempt["attempt_id"])).score) == 10


@pytest.mark.parametrize("failure", ["validation", "grading"])
def test_lock_failure_rolls_back(client, db_session, room, monkeypatch, failure):
    student, attempt, path = setup_attempt(client, room)
    db_session.get(Exam, UUID(room[-1]["id"])).max_tab_violations = 1
    db_session.commit()
    answers = [{"question_id": str(room[3].id), "selected_options": ["A"]}]
    if failure == "validation":
        answers[0]["question_id"] = str(uuid4())
    else:
        def fail(*args):
            from fastapi import HTTPException
            raise HTTPException(503, "grading unavailable")
        monkeypatch.setattr(service, "grade_attempt", fail)
    response = client.post(path, headers=headers(student), json=payload(answers=answers))
    assert response.status_code == (400 if failure == "validation" else 503)
    db_session.expire_all()
    saved = db_session.get(ExamAttempt, UUID(attempt["attempt_id"]))
    assert saved.status == AttemptStatus.IN_PROGRESS
    assert saved.violation_count == 0 and saved.submitted_at is None
    assert db_session.query(AntiCheatLog).count() == 0
    assert db_session.query(AttemptAnswer).count() == 0


@pytest.mark.parametrize("bad", [{"event_type": "FAKE"}, {"metadata_info": []}, {"event_id": "bad"}, {"answers": "bad"}])
def test_payload_validation(client, room, bad):
    student, _, path = setup_attempt(client, room)
    assert client.post(path, headers=headers(student), json={**payload(), **bad}).status_code == 422


def test_auth_ownership_origin(client, db_session, room):
    student, _, path = setup_attempt(client, room)
    assert client.post(path, json=payload()).status_code == 401
    assert client.post(path, headers=headers(room[0]), json=payload()).status_code == 403
    other = User(email="anti-other@example.com", full_name="Other", role=UserRole.STUDENT, password_hash="unused")
    db_session.add(other); db_session.commit()
    assert client.post(path, headers=headers(other), json=payload()).status_code == 403
    assert client.post(path, headers={**headers(student), "Origin": "https://untrusted.invalid"}, json=payload()).status_code == 403
    assert db_session.query(AntiCheatLog).count() == 0


def test_expired_event_does_not_accept_late_answers(client, db_session, room, monkeypatch):
    student, attempt, path = setup_attempt(client, room)
    deadline = service.aware(db_session.get(ExamAttempt, UUID(attempt["attempt_id"])).expires_at)
    monkeypatch.setattr(service, "now", lambda: deadline + timedelta(seconds=1))
    response = client.post(path, headers=headers(student), json=payload(answers=[{"question_id": str(room[3].id), "selected_options": ["A"]}]))
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "EXPIRED"
    assert response.json()["data"]["violation_count"] == 0
    assert db_session.query(AntiCheatLog).count() == 0
    assert db_session.query(AttemptAnswer).one().selected_options == []
    assert float(db_session.get(ExamAttempt, UUID(attempt["attempt_id"])).score) == 0
