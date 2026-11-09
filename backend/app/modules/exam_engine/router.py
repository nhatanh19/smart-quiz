from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import require_roles
from app.models.entities import UserRole
from app.schemas.common import APIResponse, HealthCheckResponse

router = APIRouter(prefix="/exam-engine", tags=["Module 3: Online Exam Engine & Anti-cheat (Dev 3)"])


@router.get("/health", response_model=HealthCheckResponse)
def exam_engine_health_check():
    """Health check endpoint for Exam Engine module."""
    return HealthCheckResponse(service="Online Exam Engine & Anti-cheat Service")


# ==============================================================================
# PLACEHOLDER ENDPOINTS FOR DEV 3
# ==============================================================================


@router.post("/exams/{exam_id}/start", response_model=APIResponse[dict], dependencies=[Depends(require_roles([UserRole.STUDENT]))])
def start_exam_placeholder(exam_id: int, db: Session = Depends(get_db)):
    """Start exam attempt placeholder.

    // TODO: Dev 3 - Validate start/end time, access password, attempt limits,
    // shuffle questions and options, and persist question_order_snapshot.
    """
    return APIResponse(
        success=True,
        message="// TODO: Dev 3 - Implement Exam Start & Shuffling logic",
        data={"attempt_id": 0, "exam_id": exam_id, "questions": []},
    )


@router.post("/attempts/{attempt_id}/submit", response_model=APIResponse[dict], dependencies=[Depends(require_roles([UserRole.STUDENT]))])
def submit_exam_placeholder(attempt_id: int, db: Session = Depends(get_db)):
    """Submit exam attempt placeholder.

    // TODO: Dev 3 - Save student responses into attempt_answers, mark status
    // as SUBMITTED, and trigger auto-grading in Module 4.
    """
    return APIResponse(
        success=True,
        message="// TODO: Dev 3 - Implement Exam Submit logic",
        data={"attempt_id": attempt_id, "status": "SUBMITTED"},
    )


@router.post("/attempts/{attempt_id}/log-violation", response_model=APIResponse[dict], dependencies=[Depends(require_roles([UserRole.STUDENT]))])
def log_violation_placeholder(attempt_id: int, db: Session = Depends(get_db)):
    """Log anti-cheat violation placeholder.

    // TODO: Dev 3 - Log TAB_SWITCH, WINDOW_BLUR, or COPY_PASTE events into
    // anti_cheat_logs table. If violation_count >= max_tab_violations, lock attempt.
    """
    return APIResponse(
        success=True,
        message="// TODO: Dev 3 - Implement Anti-cheat logging & auto-lock threshold logic",
        data={"attempt_id": attempt_id, "violation_count": 1},
    )
