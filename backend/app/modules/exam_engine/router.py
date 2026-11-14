from uuid import UUID
import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, Response, Query
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.core.security import require_roles, verify_password
from app.models.entities import User, UserRole, Exam
from app.schemas.common import APIResponse, HealthCheckResponse
from app.modules.auth.router import check_origin
from app.modules.exam_engine.schemas import ExamInput, JoinInput, SubmitInput, ViolationInput
from app.modules.exam_engine import service

router = APIRouter(prefix="/exam-engine", tags=["Exam Engine"])
manager = require_roles([UserRole.INSTRUCTOR, UserRole.ADMIN])
student = require_roles([UserRole.STUDENT])
grant_path = f"{settings.API_V1_STR}/exam-engine"


def verify_entry(request: Request, exam: Exam, user: User):
    try:
        data = jwt.decode(request.cookies.get(f"exam_entry_{exam.id}", ""), settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM], options={"require": ["exp", "sub", "type", "exam_id", "version"]})
        if (data["type"] != "exam_entry" or data["sub"] != str(user.id) or
                data["exam_id"] != str(exam.id) or data["version"] != exam.updated_at.isoformat()):
            raise ValueError()
    except (jwt.PyJWTError, ValueError):
        raise HTTPException(403, "Vui lòng nhập mã phòng và PIN để vào ca thi.")


@router.get("/health", response_model=HealthCheckResponse)
def health():
    return HealthCheckResponse(service="Exam Engine")


@router.post("/exams", status_code=201)
def create(payload: ExamInput, db: Session = Depends(get_db), user: User = Depends(manager), origin=Depends(check_origin)):
    try:
        return APIResponse(data=service.save_exam(db, payload, user))
    except Exception:
        db.rollback()
        raise


@router.get("/exams")
def list_exams(skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100), db: Session = Depends(get_db), user: User = Depends(manager)):
    query = db.query(Exam)
    if user.role != UserRole.ADMIN:
        query = query.filter(Exam.instructor_id == user.id)
    return APIResponse(data=[service.public_exam(e) for e in query.order_by(Exam.created_at.desc()).offset(skip).limit(limit).all()])


@router.get("/exams/{exam_id}")
def detail(exam_id: UUID, db: Session = Depends(get_db), user: User = Depends(manager)):
    exam = service.get_exam(db, exam_id)
    service.require_owner(exam, user)
    data = service.public_exam(exam)
    data["questions"] = [{"question_id": r.question_id, "points": r.points} for r in service.rows(db, exam.id)]
    return APIResponse(data=data)


@router.put("/exams/{exam_id}")
def update(exam_id: UUID, payload: ExamInput, db: Session = Depends(get_db), user: User = Depends(manager), origin=Depends(check_origin)):
    try:
        return APIResponse(data=service.save_exam(db, payload, user, exam_id))
    except Exception:
        db.rollback()
        raise


@router.post("/exams/join")
def join(payload: JoinInput, response: Response, db: Session = Depends(get_db), user: User = Depends(student), origin=Depends(check_origin)):
    exam = db.query(Exam).filter(Exam.exam_code == payload.exam_code.strip().upper()).first()
    if not exam or (exam.access_password_hash and (len(payload.pin.encode("utf-8")) > 72 or not verify_password(payload.pin, exam.access_password_hash))):
        raise HTTPException(403, "Mã phòng hoặc PIN không đúng.")
    service.check_lobby(exam)
    expires = service.aware(exam.end_time)
    token = jwt.encode({"sub": str(user.id), "exam_id": str(exam.id), "type": "exam_entry",
        "version": exam.updated_at.isoformat(), "exp": expires}, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    response.set_cookie(f"exam_entry_{exam.id}", token, httponly=True, secure=settings.COOKIE_SECURE,
        samesite="lax", path=grant_path, max_age=max(1, int((expires-service.now()).total_seconds())))
    response.headers["Cache-Control"] = "no-store"
    return APIResponse(data=service.public_exam(exam))


@router.get("/exams/{exam_id}/lobby")
def lobby(exam_id: UUID, request: Request, response: Response, db: Session = Depends(get_db), user: User = Depends(student)):
    exam = service.get_exam(db, exam_id)
    verify_entry(request, exam, user)
    service.check_lobby(exam)
    response.headers["Cache-Control"] = "no-store"
    return APIResponse(data=service.public_exam(exam))


@router.post("/exams/{exam_id}/start")
def start(exam_id: UUID, request: Request, response: Response, db: Session = Depends(get_db), user: User = Depends(student), origin=Depends(check_origin)):
    try:
        exam = service.get_exam(db, exam_id, lock=True)
        verify_entry(request, exam, user)
        response.headers["Cache-Control"] = "no-store"
        return APIResponse(data=service.start_attempt(db, exam_id, user))
    except Exception:
        db.rollback()
        raise


@router.post("/attempts/{attempt_id}/submit")
def submit(attempt_id: UUID, payload: SubmitInput, response: Response, db: Session = Depends(get_db), user: User = Depends(student), origin=Depends(check_origin)):
    try:
        response.headers["Cache-Control"] = "no-store"
        return APIResponse(data=service.submit_attempt(db, attempt_id, user, payload))
    except Exception:
        db.rollback()
        raise


@router.get("/attempts/{attempt_id}")
def attempt_detail(attempt_id: UUID, response: Response, db: Session = Depends(get_db), user: User = Depends(student)):
    response.headers["Cache-Control"] = "no-store"
    return APIResponse(data=service.get_attempt(db, attempt_id, user))


@router.post("/attempts/{attempt_id}/answers")
def save_answers(attempt_id: UUID, payload: SubmitInput, response: Response, db: Session = Depends(get_db), user: User = Depends(student), origin=Depends(check_origin)):
    try:
        response.headers["Cache-Control"] = "no-store"
        return APIResponse(data=service.save_answers(db, attempt_id, user, payload))
    except Exception:
        db.rollback()
        raise


@router.post("/attempts/{attempt_id}/log-violation")
def log_violation(attempt_id: UUID, payload: ViolationInput, response: Response, db: Session = Depends(get_db), user: User = Depends(student), origin=Depends(check_origin)):
    try:
        response.headers["Cache-Control"] = "no-store"
        return APIResponse(data=service.log_violation(db, attempt_id, user, payload))
    except Exception:
        db.rollback()
        raise
