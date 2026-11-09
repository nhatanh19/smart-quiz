"""Exam persistence and the #13 -> #14 transaction boundary."""
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
import secrets
import string
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.exc import IntegrityError

from app.core.security import get_password_hash
from app.models.entities import Exam, ExamQuestion, ExamAttempt, AttemptAnswer, AttemptStatus, Question, User, UserRole
from app.modules.exam_engine.schemas import ExamInput, SubmitInput
from app.modules.exam_engine.shuffle_service import build_attempt_snapshot, render_attempt_questions, validate_attempt_answers
from app.modules.tutor_analytics.services.grading_service import grade_attempt


def now():
    return datetime.now(timezone.utc)


def aware(value):
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def get_exam(db, exam_id, *, lock=False):
    query = db.query(Exam).filter(Exam.id == exam_id)
    if lock:
        query = query.with_for_update()
    exam = query.first()
    if not exam:
        raise HTTPException(404, "Không tìm thấy ca thi.")
    return exam


def require_owner(exam, user):
    if user.role != UserRole.ADMIN and exam.instructor_id != user.id:
        raise HTTPException(403, "Bạn không quản lý ca thi này.")


def public_exam(exam):
    return {"id": exam.id, "exam_code": exam.exam_code, "title": exam.title,
            "description": exam.description, "duration_minutes": exam.duration_minutes,
            "start_time": aware(exam.start_time) if exam.start_time else None,
            "end_time": aware(exam.end_time) if exam.end_time else None,
            "max_attempts": exam.max_attempts, "shuffle_questions": exam.shuffle_questions,
            "shuffle_options": exam.shuffle_options, "is_published": exam.is_published,
            "requires_pin": bool(exam.access_password_hash)}


def save_exam(db: Session, payload: ExamInput, user: User, exam_id=None):
    exam = get_exam(db, exam_id, lock=True) if exam_id else None
    if exam:
        require_owner(exam, user)
        if db.query(ExamAttempt).filter(ExamAttempt.exam_id == exam.id).first():
            raise HTTPException(409, "Không thể sửa ca thi đã có lượt làm.")
    ids = [item.question_id for item in payload.questions]
    questions = db.query(Question).filter(Question.id.in_(ids)).order_by(Question.id).with_for_update().all()
    if len(questions) != len(ids):
        raise HTTPException(400, "Có câu hỏi không tồn tại.")
    if user.role != UserRole.ADMIN and any(q.creator_id != user.id for q in questions):
        raise HTTPException(403, "Không được sử dụng câu hỏi của giảng viên khác.")
    fields = payload.model_dump(exclude={"questions", "pin"})
    fields["access_password_hash"] = get_password_hash(payload.pin) if payload.pin else None
    if exam:
        for key, value in fields.items():
            setattr(exam, key, value)
        db.query(ExamQuestion).filter(ExamQuestion.exam_id == exam.id).delete(synchronize_session=False)
    else:
        # The unique constraint remains authoritative even if random codes collide.
        for _ in range(5):
            code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
            candidate = Exam(**fields, instructor_id=user.id, exam_code=code)
            try:
                with db.begin_nested():
                    db.add(candidate)
                    db.flush()
                exam = candidate
                break
            except IntegrityError:
                if db.query(Exam).filter(Exam.exam_code == code).first() is None:
                    raise
        if exam is None:
            raise HTTPException(409, "Chưa thể sinh mã phòng, vui lòng thử lại.")
    for index, item in enumerate(payload.questions, 1):
        db.add(ExamQuestion(exam_id=exam.id, question_id=item.question_id, order_index=index, points=item.points))
    db.commit()
    db.refresh(exam)
    return public_exam(exam)


def check_lobby(exam):
    if not exam.is_published:
        raise HTTPException(403, "Ca thi chưa được công bố.")
    if now() >= aware(exam.end_time):
        raise HTTPException(403, "Ca thi đã đóng.")


def rows(db, exam_id):
    return db.query(ExamQuestion).options(selectinload(ExamQuestion.question)).filter(
        ExamQuestion.exam_id == exam_id).order_by(ExamQuestion.order_index).all()


def start_attempt(db, exam_id, user):
    # Exam lock serializes starts and configuration changes; DB unique indexes are a second guard.
    exam = get_exam(db, exam_id, lock=True)
    check_lobby(exam)
    timestamp = now()
    if timestamp < aware(exam.start_time):
        raise HTTPException(403, "Ca thi chưa bắt đầu.")
    attempts = db.query(ExamAttempt).filter(ExamAttempt.exam_id == exam.id, ExamAttempt.student_id == user.id).all()
    active = next((item for item in attempts if item.status == AttemptStatus.IN_PROGRESS), None)
    if active and timestamp >= aware(active.expires_at):
        active.status = AttemptStatus.EXPIRED
        active.submitted_at = active.expires_at
        db.flush()
        active = None
    if not active and len(attempts) >= exam.max_attempts:
        # Persist expiry even when no further attempt is allowed.
        db.commit()
        raise HTTPException(403, "Bạn đã hết lượt làm bài.")
    exam_rows = rows(db, exam.id)
    if not exam_rows:
        raise HTTPException(409, "Ca thi chưa có câu hỏi.")
    # Coordinate with Question Bank edits, then reload source after acquiring locks.
    db.query(Question).filter(Question.id.in_([r.question_id for r in exam_rows])).order_by(
        Question.id).populate_existing().with_for_update().all()
    if active is None:
        number = max((a.attempt_number for a in attempts), default=0) + 1
        snapshot = build_attempt_snapshot(exam_rows, user.id, exam.id, number,
            shuffle_questions=exam.shuffle_questions, shuffle_options=exam.shuffle_options)
        active = ExamAttempt(exam_id=exam.id, student_id=user.id, attempt_number=number,
            started_at=timestamp, expires_at=min(timestamp + timedelta(minutes=exam.duration_minutes), aware(exam.end_time)),
            question_order_snapshot=snapshot)
        db.add(active)
        db.flush()
    questions = render_attempt_questions(active.question_order_snapshot, exam_rows)
    data = {"attempt_id": active.id, "expires_at": aware(active.expires_at), "duration_minutes": exam.duration_minutes,
            "questions": questions, "status": active.status.value, "exam_id": exam.id}
    db.commit()
    return data


def submit_attempt(db, attempt_id: UUID, user, payload: SubmitInput):
    attempt = db.query(ExamAttempt).filter(ExamAttempt.id == attempt_id).with_for_update().first()
    if not attempt:
        raise HTTPException(404, "Không tìm thấy bài làm.")
    if attempt.student_id != user.id:
        raise HTTPException(403, "Bài làm không thuộc tài khoản của bạn.")
    if attempt.status != AttemptStatus.IN_PROGRESS:
        raise HTTPException(409, "Bài làm đã kết thúc.")
    if now() >= aware(attempt.expires_at):
        attempt.status = AttemptStatus.EXPIRED
        attempt.submitted_at = attempt.expires_at
        db.commit()
        raise HTTPException(409, "Đã hết thời gian làm bài.")
    answers = [item.model_dump() for item in payload.answers]
    try:
        validate_attempt_answers(attempt.question_order_snapshot, answers)
    except ValueError as error:
        raise HTTPException(400, str(error)) from error
    existing = {a.question_id: a for a in db.query(AttemptAnswer).filter(AttemptAnswer.attempt_id == attempt.id).all()}
    for answer in answers:
        record = existing.get(answer["question_id"])
        if record is None:
            record = AttemptAnswer(attempt_id=attempt.id, **answer)
            db.add(record)
        else:
            record.selected_options = answer["selected_options"]
    db.flush()
    result = grade_attempt(db, attempt.id)
    db.commit()
    return {**asdict(result), "status": attempt.status.value}
