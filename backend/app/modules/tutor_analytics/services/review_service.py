"""Service providing Post-Exam Review Mode data and analytics (Issue #15, WBS 5.1.2)."""

import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session, joinedload

from app.models.entities import (
    AttemptAnswer,
    AttemptStatus,
    Exam,
    ExamAttempt,
    ExamQuestion,
    Question,
    User,
    UserRole,
)
from app.modules.tutor_analytics.exceptions import (
    InvalidAttemptStateError,
    NotFoundError,
)


def get_exam_review_data(
    db: Session,
    attempt_id: uuid.UUID,
    current_user: Optional[User] = None,
) -> Dict[str, Any]:
    """Retrieve detailed exam review data for a completed exam attempt.

    Adheres strictly to DEV3_DEV4_WORKING_AGREEMENT Section 5.3 (B2):
    - Requires attempt to be finished (not IN_PROGRESS).
    - Checks authorization: STUDENT can only review own attempt; INSTRUCTOR/ADMIN can review any attempt.
    - Honors question and option order from `question_order_snapshot` (Seed-based Shuffling, Issue #13).
    - Returns summary score, correct/incorrect counters, and detailed question-by-question breakdown.
    """
    attempt = (
        db.query(ExamAttempt)
        .options(joinedload(ExamAttempt.student), joinedload(ExamAttempt.exam))
        .filter(ExamAttempt.id == attempt_id)
        .first()
    )
    if not attempt:
        raise NotFoundError(f"Exam attempt with id '{attempt_id}' not found.")

    # Authorization check
    if current_user:
        if current_user.role == UserRole.STUDENT and attempt.student_id != current_user.id:
            raise PermissionError("Bạn không có quyền xem lại bài làm của thí sinh khác.")

    # State validation: Cannot review while in progress
    if attempt.status == AttemptStatus.IN_PROGRESS:
        raise InvalidAttemptStateError("Bài thi đang trong thời gian làm và chưa được nộp.")

    exam = attempt.exam or db.query(Exam).filter(Exam.id == attempt.exam_id).first()
    exam_title = exam.title if exam else "Bài kiểm tra"

    # Query all submitted answers
    answers = (
        db.query(AttemptAnswer)
        .filter(AttemptAnswer.attempt_id == attempt_id)
        .all()
    )
    answers_by_qid = {ans.question_id: ans for ans in answers}

    questions_review: List[Dict[str, Any]] = []
    snapshot = attempt.question_order_snapshot

    if snapshot and isinstance(snapshot, dict) and bool(snapshot.get("questions")):
        # 1. Order questions & options based on student's snapshot
        for item in snapshot["questions"]:
            try:
                raw_qid = item.get("question_id")
                q_id = uuid.UUID(str(raw_qid)) if raw_qid else None
            except Exception:
                continue

            if not q_id:
                continue

            q = db.query(Question).filter(Question.id == q_id).first()
            if not q:
                continue

            ans = answers_by_qid.get(q_id)
            raw_options = q.options if isinstance(q.options, list) else []

            # Reorder options according to snapshot options_order
            options_order = item.get("options_order", [])
            opt_map = {opt.get("id"): opt for opt in raw_options}
            ordered_options = []
            for opt_id in options_order:
                if opt_id in opt_map:
                    ordered_options.append(opt_map[opt_id])
            for opt in raw_options:
                if opt not in ordered_options:
                    ordered_options.append(opt)

            correct_opts = [
                opt.get("id") for opt in raw_options if opt.get("is_correct") is True
            ]
            selected_opts = ans.selected_options if (ans and ans.selected_options) else []

            questions_review.append({
                "question_id": str(q.id),
                "content": q.content,
                "question_type": q.question_type.value if hasattr(q.question_type, "value") else str(q.question_type),
                "cognitive_level": q.cognitive_level.value if hasattr(q.cognitive_level, "value") else str(q.cognitive_level),
                "options": ordered_options,
                "selected_options": selected_opts,
                "correct_options": correct_opts,
                "is_correct": bool(ans.is_correct) if ans else False,
                "points_awarded": float(ans.points_awarded) if (ans and ans.points_awarded is not None) else 0.0,
                "explanation": q.explanation,
                "ai_tutor_feedback": ans.ai_tutor_feedback if ans else None,
                "order_index": len(questions_review) + 1,
            })
    else:
        # 2. Fallback: Query ExamQuestions in order_index sequence
        eq_list = (
            db.query(ExamQuestion)
            .options(joinedload(ExamQuestion.question))
            .filter(ExamQuestion.exam_id == attempt.exam_id)
            .order_by(ExamQuestion.order_index.asc())
            .all()
        )
        for eq in eq_list:
            q = eq.question
            if not q:
                continue
            ans = answers_by_qid.get(q.id)
            raw_options = q.options if isinstance(q.options, list) else []
            correct_opts = [
                opt.get("id") for opt in raw_options if opt.get("is_correct") is True
            ]
            selected_opts = ans.selected_options if (ans and ans.selected_options) else []
            questions_review.append({
                "question_id": str(q.id),
                "content": q.content,
                "question_type": q.question_type.value if hasattr(q.question_type, "value") else str(q.question_type),
                "cognitive_level": q.cognitive_level.value if hasattr(q.cognitive_level, "value") else str(q.cognitive_level),
                "options": raw_options,
                "selected_options": selected_opts,
                "correct_options": correct_opts,
                "is_correct": bool(ans.is_correct) if ans else False,
                "points_awarded": float(ans.points_awarded) if (ans and ans.points_awarded is not None) else 0.0,
                "explanation": q.explanation,
                "ai_tutor_feedback": ans.ai_tutor_feedback if ans else None,
                "order_index": eq.order_index,
            })

    # If neither snapshot nor exam_questions matched, fallback to answers
    if not questions_review and answers:
        for idx, ans in enumerate(answers, start=1):
            q = db.query(Question).filter(Question.id == ans.question_id).first()
            if not q:
                continue
            raw_options = q.options if isinstance(q.options, list) else []
            correct_opts = [
                opt.get("id") for opt in raw_options if opt.get("is_correct") is True
            ]
            questions_review.append({
                "question_id": str(q.id),
                "content": q.content,
                "question_type": q.question_type.value if hasattr(q.question_type, "value") else str(q.question_type),
                "cognitive_level": q.cognitive_level.value if hasattr(q.cognitive_level, "value") else str(q.cognitive_level),
                "options": raw_options,
                "selected_options": ans.selected_options or [],
                "correct_options": correct_opts,
                "is_correct": bool(ans.is_correct),
                "points_awarded": float(ans.points_awarded) if ans.points_awarded is not None else 0.0,
                "explanation": q.explanation,
                "ai_tutor_feedback": ans.ai_tutor_feedback,
                "order_index": idx,
            })

    total_q = len(questions_review)
    correct_count = sum(1 for q in questions_review if q["is_correct"])
    incorrect_count = total_q - correct_count

    time_spent = 0
    if attempt.started_at and attempt.submitted_at:
        time_spent = max(0, int((attempt.submitted_at - attempt.started_at).total_seconds()))

    student_name = attempt.student.full_name if attempt.student else "Sinh viên"

    return {
        "attempt_id": str(attempt.id),
        "exam_id": str(attempt.exam_id),
        "exam_title": exam_title,
        "student_id": str(attempt.student_id),
        "student_name": student_name,
        "score": attempt.score,
        "max_score": 10.0,
        "status": attempt.status.value if hasattr(attempt.status, "value") else str(attempt.status),
        "started_at": attempt.started_at.isoformat() if attempt.started_at else None,
        "submitted_at": attempt.submitted_at.isoformat() if attempt.submitted_at else None,
        "time_spent_seconds": time_spent,
        "total_questions": total_q,
        "correct_count": correct_count,
        "incorrect_count": incorrect_count,
        "questions_review": questions_review,
    }
