from dataclasses import asdict
from typing import Any, Dict, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_roles
from app.models.entities import AttemptAnswer, Exam, ExamAttempt, Question, User, UserRole
from app.modules.tutor_analytics.exceptions import (
    InvalidAttemptStateError,
    NotFoundError,
    SnapshotMismatchError,
)
from app.modules.tutor_analytics.schemas import (
    AITutorExplanationData,
    AITutorExplanationRequest,
    GradingResultSchema,
    KnowledgeGapDiagnosticResponse,
)
from app.modules.tutor_analytics.service import ai_tutor_service
from app.modules.tutor_analytics.services.grading_service import grade_attempt
from app.modules.tutor_analytics.services.knowledge_gap_service import diagnose_knowledge_gaps
from app.modules.tutor_analytics.services.review_service import get_exam_review_data
from app.schemas.common import APIResponse, HealthCheckResponse

router = APIRouter(prefix="/tutor-analytics", tags=["Module 4: AI Tutor & Analytics (Dev 4)"])


def authorize_exam(db: Session, exam_id: uuid.UUID, user: User) -> Exam:
    exam = db.get(Exam, exam_id)
    if not exam:
        raise HTTPException(404, "Không tìm thấy đề thi.")
    if user.role != UserRole.ADMIN and exam.instructor_id != user.id:
        raise HTTPException(403, "Bạn không có quyền truy cập đề thi này.")
    return exam


def authorize_attempt(
    db: Session, attempt_id: uuid.UUID, user: User, *, enforce_finished: bool = True
) -> ExamAttempt:
    attempt = db.get(ExamAttempt, attempt_id)
    if not attempt:
        raise HTTPException(404, "Không tìm thấy bài làm.")
    if user.role == UserRole.STUDENT:
        if attempt.student_id != user.id:
            raise HTTPException(403, "Bạn không có quyền truy cập bài làm này.")
        if enforce_finished and attempt.status.value == "IN_PROGRESS":
            raise HTTPException(403, "Chưa thể xem đáp án khi đang làm bài.")
    else:
        authorize_exam(db, attempt.exam_id, user)
    return attempt


def authorize_attempt_question(db: Session, attempt_id: uuid.UUID, question_id: uuid.UUID, user: User):
    attempt = authorize_attempt(db, attempt_id, user)
    questions = (attempt.question_order_snapshot or {}).get("questions", [])
    if not any(item.get("question_id") == str(question_id) for item in questions):
        raise HTTPException(403, "Câu hỏi không thuộc bài làm này.")


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
)
def grade_attempt_endpoint(
    attempt_id: uuid.UUID,
    force: bool = Query(False, description="Force re-grading of an already submitted attempt"),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles([UserRole.INSTRUCTOR, UserRole.ADMIN])),
):
    """B1: Instructor/Admin re-grading or manual grading endpoint.

    Adheres to DEV3_DEV4_WORKING_AGREEMENT section 5.3 and 7.1.
    """
    authorize_attempt(db, attempt_id, user)
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
    user: User = Depends(get_current_user),
):
    """Generate or retrieve contextual explanation for a quiz question.

    Fulfills Issue #16 (Acceptance Criteria):
    - Explains why the student-selected option is incorrect (diagnosing misconception).
    - Explains why the standard answer key is correct.
    - Pedagogical tone, easily understandable.
    - Sub-3-second response time.
    - Automatically persists generated feedback into attempt_answers.ai_tutor_feedback.
    """
    if request.attempt_id:
        if not request.question_id:
            raise HTTPException(422, "Vui lòng cung cấp mã câu hỏi trong bài làm.")
        authorize_attempt_question(db, request.attempt_id, request.question_id, user)
    elif request.question_id:
        question = db.get(Question, request.question_id)
        if not question:
            raise HTTPException(404, "Không tìm thấy câu hỏi.")
        if user.role != UserRole.ADMIN and (user.role != UserRole.INSTRUCTOR or question.creator_id != user.id):
            raise HTTPException(403, "Bạn không có quyền truy cập câu hỏi này.")
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
    user: User = Depends(get_current_user),
):
    """Generate or retrieve AI explanation specifically for a question within an exam attempt."""
    authorize_attempt_question(db, attempt_id, question_id, user)
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


# ==============================================================================
# ISSUE #15: POST-EXAM DETAILED REVIEW MODE (WBS 5.1.2)
# ==============================================================================


@router.get("/review/{attempt_id}", response_model=APIResponse[Dict[str, Any]])
def get_attempt_review(
    attempt_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve detailed exam review mode for a finished attempt.

    Connects Issue #15 (Review Mode Interface) & Issue #16 (AI Tutor Feedback).
    - Verifies attempt is submitted/finished.
    - Role check: Student views own attempt; Instructor views attempts of own exams; Admin views all.
    - Preserves question/options ordering from question_order_snapshot.
    """
    # Issue #4: check ownership/role first (STUDENT own, INSTRUCTOR own exam, ADMIN all).
    # IN_PROGRESS is then rejected with 400 by the Issue #15 review service.
    authorize_attempt(db, attempt_id, current_user, enforce_finished=False)
    try:
        data = get_exam_review_data(db, attempt_id, current_user=current_user)
        return APIResponse(
            success=True,
            message="Review mode data retrieved successfully",
            data=data,
        )
    except NotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err),
        )
    except PermissionError as err:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(err),
        )
    except InvalidAttemptStateError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi tải giao diện xem lại bài thi: {str(exc)}",
        )


# ==============================================================================
# ISSUE #17: KNOWLEDGE GAP DIAGNOSTIC CARD API (WBS 5.2.2)
# ==============================================================================


@router.get(
    "/knowledge-gaps/{attempt_id}",
    response_model=APIResponse[KnowledgeGapDiagnosticResponse],
)
def get_knowledge_gap_diagnosis(
    attempt_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Diagnose student knowledge gaps and provide actionable study advice.

    Fulfills Issue #17 (Acceptance Criteria):
    - Summarizes incorrect answers by topic/tag.
    - Explicitly surfaces: "Chủ đề bạn cần củng cố: <Tên chủ đề>"
    - Proposes at least 2 concrete study suggestions to improve outcomes.
    """
    try:
        data = diagnose_knowledge_gaps(db, attempt_id, current_user=current_user)
        return APIResponse(
            success=True,
            message="Knowledge gap diagnostic generated successfully",
            data=data,
        )
    except NotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err),
        )
    except PermissionError as err:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(err),
        )
    except InvalidAttemptStateError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi phân tích lỗ hổng kiến thức: {str(exc)}",
        )


# ==============================================================================
# PLACEHOLDER ENDPOINTS FOR REMAINING TASKS (ISSUES 27, 28)
# ==============================================================================


@router.get("/analytics/student/{student_id}", response_model=APIResponse[dict])
def get_student_analytics_placeholder(student_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Student performance analytics dashboard placeholder.

    // TODO: Dev 4 - Calculate progress trends, accuracy percentage by topic/category,
    // and identify knowledge gaps.
    """
    if user.role != UserRole.ADMIN and student_id != user.id:
        raise HTTPException(403, "Bạn không có quyền xem thống kê của người dùng này.")
    return APIResponse(
        success=True,
        message="// TODO: Dev 4 - Implement Student Learning Analytics logic",
        data={"student_id": str(student_id), "trends": [], "weak_topics": []},
    )


@router.get("/analytics/exam/{exam_id}", response_model=APIResponse[dict])
def get_exam_analytics_placeholder(exam_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(require_roles([UserRole.INSTRUCTOR, UserRole.ADMIN]))):
    """Instructor exam distribution analytics placeholder.

    // TODO: Dev 4 - Compute score distribution histogram, question difficulty
    // breakdown, and high-frequency incorrect answers.
    """
    authorize_exam(db, exam_id, user)
    return APIResponse(
        success=True,
        message="// TODO: Dev 4 - Implement Instructor Exam Analytics logic",
        data={"exam_id": str(exam_id), "score_distribution": {}, "difficult_questions": []},
    )
