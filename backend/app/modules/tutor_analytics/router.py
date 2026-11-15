import csv
from dataclasses import asdict
import io
from typing import Any, Dict, List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
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
    AccessibleExamItemSchema,
    AITutorExplanationData,
    AITutorExplanationRequest,
    ExamAnalyticsResponseSchema,
    GradingResultSchema,
    StudentAnalyticsResponseSchema,
    KnowledgeGapDiagnosticResponse,
)
from app.modules.tutor_analytics.service import ai_tutor_service
from app.modules.tutor_analytics.services.analytics_service import (
    get_exam_distribution_analytics,
    get_student_learning_analytics,
    list_accessible_exams_for_instructor,
)
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
# ISSUE #36: LEARNING ANALYTICS & SCORE DISTRIBUTION DASHBOARD (WBS 5.3)
# ==============================================================================


@router.get(
    "/analytics/instructor/exams",
    response_model=APIResponse[List[AccessibleExamItemSchema]],
    dependencies=[Depends(require_roles([UserRole.INSTRUCTOR, UserRole.ADMIN]))],
)
def get_instructor_accessible_exams(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve list of exams managed by current instructor/admin for the dashboard dropdown selector."""
    exams = list_accessible_exams_for_instructor(db, current_user)
    return APIResponse(
        success=True,
        message="Danh sách đề thi được quản lý tải thành công.",
        data=exams,
    )


@router.get(
    "/analytics/student/{student_id}",
    response_model=APIResponse[StudentAnalyticsResponseSchema],
)
def get_student_learning_analytics_endpoint(
    student_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Student performance analytics dashboard (Issue #36 / WBS 5.3.1).

    RBAC & Ownership:
    - STUDENT: Only permitted to view their own analytics.
    - INSTRUCTOR / ADMIN: Permitted to view analytics for any student.
    Calculates progress trends, accuracy percentage by topic/category,
    and identifies knowledge gaps.
    """
    try:
        if student_id == "me":
            target_uuid = current_user.id
        else:
            target_uuid = uuid.UUID(student_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"student_id '{student_id}' không phải định dạng UUID hợp lệ.",
        )

    try:
        data = get_student_learning_analytics(db, target_uuid, current_user=current_user)
        return APIResponse(
            success=True,
            message="Dữ liệu thống kê tiến độ học tập của sinh viên tải thành công.",
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
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi tính toán phân tích học tập sinh viên: {str(exc)}",
        )


@router.get(
    "/analytics/exam/{exam_id}",
    response_model=APIResponse[ExamAnalyticsResponseSchema],
)
def get_exam_distribution_analytics_endpoint(
    exam_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Instructor exam distribution analytics (Issue #36 / WBS 5.3.2).

    RBAC & Ownership:
    - STUDENT: Forbidden (403).
    - INSTRUCTOR: Permitted only for exams they created/own.
    - ADMIN: Permitted for any exam.
    Computes score distribution histogram, summary statistics, top difficult questions,
    and student score sheet.
    """
    try:
        exam_uuid = uuid.UUID(exam_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"exam_id '{exam_id}' không phải định dạng UUID hợp lệ.",
        )

    try:
        data = get_exam_distribution_analytics(db, exam_uuid, current_user=current_user)
        return APIResponse(
            success=True,
            message="Dữ liệu phổ điểm và phân tích đề thi tải thành công.",
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
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi tính toán phổ điểm đề thi: {str(exc)}",
        )


@router.get(
    "/analytics/exam/{exam_id}/csv",
)
def export_exam_scores_csv(
    exam_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Export exam scoresheet to CSV format for lecturers with UTF-8 BOM encoding."""
    try:
        exam_uuid = uuid.UUID(exam_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"exam_id '{exam_id}' không phải định dạng UUID hợp lệ.",
        )

    try:
        data = get_exam_distribution_analytics(db, exam_uuid, current_user=current_user)
    except NotFoundError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err))
    except PermissionError as err:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(err))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi xuất bảng điểm CSV: {str(exc)}",
        )

    output = io.StringIO()
    # Write UTF-8 BOM for Microsoft Excel compatibility
    output.write("\ufeff")
    writer = csv.writer(output)

    writer.writerow(["Mã đề thi", data.get("exam_code", "")])
    writer.writerow(["Tên đề thi", data.get("exam_title", "")])
    writer.writerow(["Tổng số lượt thi", data.get("summary", {}).get("total_attempts", 0)])
    writer.writerow(["Điểm trung bình", data.get("summary", {}).get("avg_score", 0.0)])
    writer.writerow(["Điểm cao nhất", data.get("summary", {}).get("max_score", 0.0)])
    writer.writerow(["Điểm thấp nhất", data.get("summary", {}).get("min_score", 0.0)])
    writer.writerow([])

    writer.writerow([
        "STT",
        "Họ và tên thí sinh",
        "Email",
        "Lần thi",
        "Điểm số (thang 10)",
        "Thời gian làm bài (giây)",
        "Số lần vi phạm",
        "Thời điểm nộp bài",
        "Trạng thái",
    ])

    for idx, row in enumerate(data.get("student_scores", []), start=1):
        writer.writerow([
            idx,
            row.get("student_name", ""),
            row.get("student_email", ""),
            row.get("attempt_number", 1),
            row.get("score", 0.0),
            row.get("time_spent_seconds", 0),
            row.get("violation_count", 0),
            row.get("submitted_at", ""),
            row.get("status", ""),
        ])

    csv_content = output.getvalue()
    filename = f"bang_diem_{data.get('exam_code', exam_id)}.csv"

    return Response(
        content=csv_content.encode("utf-8-sig"),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )
