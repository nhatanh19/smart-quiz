from dataclasses import asdict
from typing import Any, Dict, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_roles
from app.models.entities import AttemptAnswer, ExamAttempt, Question, User, UserRole
from app.modules.tutor_analytics.exceptions import (
    InvalidAttemptStateError,
    NotFoundError,
    SnapshotMismatchError,
)
from app.modules.tutor_analytics.schemas import (
    AITutorExplanationData,
    AITutorExplanationRequest,
    GradingResultSchema,
)
from app.modules.tutor_analytics.service import ai_tutor_service
from app.modules.tutor_analytics.services.grading_service import grade_attempt
from app.schemas.common import APIResponse, HealthCheckResponse

router = APIRouter(prefix="/tutor-analytics", tags=["Module 4: AI Tutor & Analytics (Dev 4)"])


@router.get("/health", response_model=HealthCheckResponse)
def tutor_analytics_health_check():
    """Health check endpoint for AI Tutor & Analytics module."""
    return HealthCheckResponse(service="Auto-Grading, AI Tutor & Analytics Service")


# ==============================================================================
# ISSUE #14: INSTANT AUTO-GRADING ENGINE ENDPOINT
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


# ==============================================================================
# ISSUE #16: CONTEXTUAL EXPLANATION GENERATOR API (WBS 5.2.1)
# ==============================================================================


@router.post("/explain", response_model=APIResponse[AITutorExplanationData])
async def generate_explanation(
    request: AITutorExplanationRequest,
    db: Session = Depends(get_db),
):
    """Generate or retrieve contextual explanation for a quiz question.

    Fulfills Issue #16 (Acceptance Criteria):
    - Explains why the student-selected option is incorrect (diagnosing misconception).
    - Explains why the standard answer key is correct.
    - Pedagogical tone, easily understandable.
    - Sub-3-second response time.
    - Automatically persists generated feedback into attempt_answers.ai_tutor_feedback.
    """
    try:
        data = await ai_tutor_service.generate_explanation(request=request, db=db)
        return APIResponse(
            success=True,
            message=f"AI Tutor explanation generated in {data.response_time_ms}ms"
            + (" (cached)" if data.cached else ""),
            data=data,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate AI Tutor explanation: {str(exc)}",
        )


@router.post(
    "/attempts/{attempt_id}/questions/{question_id}/explain",
    response_model=APIResponse[AITutorExplanationData],
)
async def explain_attempt_question(
    attempt_id: uuid.UUID,
    question_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """Generate or retrieve AI explanation specifically for a question within an exam attempt."""
    request = AITutorExplanationRequest(attempt_id=attempt_id, question_id=question_id)
    try:
        data = await ai_tutor_service.generate_explanation(request=request, db=db)
        return APIResponse(
            success=True,
            message=f"AI Tutor explanation retrieved in {data.response_time_ms}ms"
            + (" (cached)" if data.cached else ""),
            data=data,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate explanation for attempt {attempt_id}: {str(exc)}",
        )


@router.get("/review/{attempt_id}", response_model=APIResponse[Dict[str, Any]])
def get_attempt_review(attempt_id: uuid.UUID, db: Session = Depends(get_db)):
    """Retrieve detailed exam review mode for a finished attempt.

    Connects Issue #15 (Review Mode) & Issue #16 (AI Tutor Feedback).
    """
    attempt = db.query(ExamAttempt).filter(ExamAttempt.id == attempt_id).first()
    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exam attempt with id '{attempt_id}' not found.",
        )

    answers = (
        db.query(AttemptAnswer)
        .filter(AttemptAnswer.attempt_id == attempt_id)
        .all()
    )

    questions_review = []
    for ans in answers:
        q = db.query(Question).filter(Question.id == ans.question_id).first()
        if not q:
            continue

        options = q.options if isinstance(q.options, list) else []
        correct_options = [
            opt.get("id") for opt in options if opt.get("is_correct") is True
        ]

        questions_review.append(
            {
                "question_id": str(q.id),
                "content": q.content,
                "question_type": q.question_type.value if hasattr(q.question_type, "value") else str(q.question_type),
                "cognitive_level": q.cognitive_level.value if hasattr(q.cognitive_level, "value") else str(q.cognitive_level),
                "options": options,
                "selected_options": ans.selected_options or [],
                "correct_options": correct_options,
                "is_correct": ans.is_correct,
                "points_awarded": ans.points_awarded,
                "ai_tutor_feedback": ans.ai_tutor_feedback,
            }
        )

    return APIResponse(
        success=True,
        message="Review mode data retrieved successfully",
        data={
            "attempt_id": str(attempt.id),
            "exam_id": str(attempt.exam_id),
            "score": attempt.score,
            "status": attempt.status.value if hasattr(attempt.status, "value") else str(attempt.status),
            "total_questions": len(questions_review),
            "correct_count": sum(1 for q in questions_review if q["is_correct"]),
            "questions_review": questions_review,
        },
    )


# ==============================================================================
# PLACEHOLDER ENDPOINTS FOR REMAINING TASKS (ISSUES 27, 28)
# ==============================================================================


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
