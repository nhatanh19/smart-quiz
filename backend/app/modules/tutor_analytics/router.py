from dataclasses import asdict
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_roles
from app.models.entities import User, UserRole
from app.modules.tutor_analytics.exceptions import (
    InvalidAttemptStateError,
    NotFoundError,
    SnapshotMismatchError,
)
from app.modules.tutor_analytics.schemas import GradingResultSchema
from app.modules.tutor_analytics.services.grading_service import grade_attempt
from app.schemas.common import APIResponse, HealthCheckResponse

router = APIRouter(prefix="/tutor-analytics", tags=["Module 4: AI Tutor & Analytics (Dev 4)"])


@router.get("/health", response_model=HealthCheckResponse)
def tutor_analytics_health_check():
    """Health check endpoint for AI Tutor & Analytics module."""
    return HealthCheckResponse(service="Auto-Grading, AI Tutor & Analytics Service")


# ==============================================================================
# ENDPOINTS FOR DEV 4
# ==============================================================================


@router.post(
    "/grade/{attempt_id}",
    response_model=APIResponse[GradingResultSchema],
    dependencies=[Depends(require_roles([UserRole.INSTRUCTOR, UserRole.ADMIN]))],
)
def grade_attempt_endpoint(
    attempt_id: uuid.UUID,
    force: bool = Query(False, description="Force re-grading of an already submitted attempt"),
    db: Session = Depends(get_db),
):
    """B1: Instructor/Admin re-grading or manual grading endpoint.
    
    Adheres to DEV3_DEV4_WORKING_AGREEMENT section 5.3 and 7.1.
    """
    try:
        result = grade_attempt(db, attempt_id, force=force)
        db.commit()
    except NotFoundError as err:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err),
        )
    except (SnapshotMismatchError, InvalidAttemptStateError) as err:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        )
    except Exception as err:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi hệ thống khi chấm điểm: {str(err)}",
        )

    return APIResponse(
        success=True,
        message="Chấm điểm bài thi thành công.",
        data=asdict(result),
    )


@router.get("/review/{attempt_id}", response_model=APIResponse[dict])
def get_review_placeholder(attempt_id: str, db: Session = Depends(get_db)):
    """Detailed exam review mode with AI Tutor feedback placeholder.

    // TODO: Dev 4 - Issue #15: Retrieve student answers vs standard answer key and provide
    // contextual AI Tutor explanations (ai_tutor_feedback).
    """
    return APIResponse(
        success=True,
        message="// TODO: Dev 4 - Implement Exam Review Mode with AI Tutor logic",
        data={"attempt_id": attempt_id, "questions_review": []},
    )


@router.get("/analytics/student/{student_id}", response_model=APIResponse[dict])
def get_student_analytics_placeholder(student_id: str, db: Session = Depends(get_db)):
    """Student performance analytics dashboard placeholder.

    // TODO: Dev 4 - Calculate progress trends, accuracy percentage by topic/category,
    // and identify knowledge gaps.
    """
    return APIResponse(
        success=True,
        message="// TODO: Dev 4 - Implement Student Learning Analytics logic",
        data={"student_id": student_id, "trends": [], "weak_topics": []},
    )


@router.get("/analytics/exam/{exam_id}", response_model=APIResponse[dict])
def get_exam_analytics_placeholder(exam_id: str, db: Session = Depends(get_db)):
    """Instructor exam distribution analytics placeholder.

    // TODO: Dev 4 - Compute score distribution histogram, question difficulty
    // breakdown, and high-frequency incorrect answers.
    """
    return APIResponse(
        success=True,
        message="// TODO: Dev 4 - Implement Instructor Exam Analytics logic",
        data={"exam_id": exam_id, "score_distribution": {}, "difficult_questions": []},
    )
