"""Analytics service for Student Progress and Lecturer Exam Distribution (Issue #36, WBS 5.3.1 & 5.3.2)."""

from datetime import datetime
import math
from typing import Any, Dict, List, Optional
import uuid

from sqlalchemy.orm import Session, joinedload

from app.models.entities import (
    AttemptAnswer,
    AttemptStatus,
    Category,
    Exam,
    ExamAttempt,
    ExamQuestion,
    Question,
    User,
    UserRole,
)
from app.modules.tutor_analytics.exceptions import NotFoundError


def _calculate_time_spent(
    started_at: Optional[datetime],
    submitted_at: Optional[datetime],
) -> int:
    """Calculate attempt duration in seconds safely across timezone awareness."""
    if not started_at or not submitted_at:
        return 0
    if started_at.tzinfo is not None and submitted_at.tzinfo is None:
        submitted_at = submitted_at.replace(tzinfo=started_at.tzinfo)
    elif started_at.tzinfo is None and submitted_at.tzinfo is not None:
        started_at = started_at.replace(tzinfo=submitted_at.tzinfo)
    seconds = int((submitted_at - started_at).total_seconds())
    return max(0, seconds)


def _compute_median(values: List[float]) -> float:
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    mid = n // 2
    if n % 2 == 1:
        return round(float(sorted_vals[mid]), 2)
    return round(float((sorted_vals[mid - 1] + sorted_vals[mid]) / 2.0), 2)


def _compute_std_dev(values: List[float], mean: float) -> float:
    if len(values) <= 1:
        return 0.0
    variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
    return round(math.sqrt(variance), 2)


def get_student_learning_analytics(
    db: Session,
    student_id: uuid.UUID,
    current_user: Optional[User] = None,
) -> Dict[str, Any]:
    """Calculate progress trends, accuracy percentage by topic/category, and knowledge gaps for a student (WBS 5.3.1).

    RBAC:
    - STUDENT: only allowed to view their own analytics.
    - INSTRUCTOR / ADMIN: allowed to view any student's analytics.
    """
    student = db.query(User).filter(User.id == student_id).first()
    if not student:
        raise NotFoundError(f"Sinh viên với ID '{student_id}' không tồn tại.")

    # Authorization Check
    if current_user:
        if current_user.role == UserRole.STUDENT and current_user.id != student_id:
            raise PermissionError("Bạn không có quyền xem dữ liệu phân tích học tập của sinh viên khác.")

    # Query completed/submitted attempts of this student
    attempts = (
        db.query(ExamAttempt)
        .options(joinedload(ExamAttempt.exam))
        .filter(
            ExamAttempt.student_id == student_id,
            ExamAttempt.status != AttemptStatus.IN_PROGRESS,
            ExamAttempt.score.isnot(None),
        )
        .order_by(ExamAttempt.started_at.asc())
        .all()
    )

    # 1. Summary Metrics
    scores = [attempt.score for attempt in attempts if attempt.score is not None]
    total_attempts = len(attempts)
    unique_exams = set(attempt.exam_id for attempt in attempts)

    avg_score = round(sum(scores) / total_attempts, 2) if total_attempts > 0 else 0.0
    highest_score = round(max(scores), 2) if total_attempts > 0 else 0.0
    lowest_score = round(min(scores), 2) if total_attempts > 0 else 0.0
    pass_count = sum(1 for s in scores if s >= 5.0)
    pass_rate = round((pass_count / total_attempts) * 100, 1) if total_attempts > 0 else 0.0

    summary = {
        "total_attempts": total_attempts,
        "total_exams": len(unique_exams),
        "average_score": avg_score,
        "highest_score": highest_score,
        "lowest_score": lowest_score,
        "pass_rate": pass_rate,
    }

    # 2. Score Trends Over Time
    trends = []
    for attempt in attempts:
        exam_title = attempt.exam.title if attempt.exam else "Bài kiểm tra"
        trends.append({
            "attempt_id": str(attempt.id),
            "exam_id": str(attempt.exam_id),
            "exam_title": exam_title,
            "attempt_number": attempt.attempt_number,
            "score": round(attempt.score, 2) if attempt.score is not None else 0.0,
            "started_at": attempt.started_at.isoformat() if attempt.started_at else None,
            "submitted_at": attempt.submitted_at.isoformat() if attempt.submitted_at else None,
            "time_spent_seconds": _calculate_time_spent(attempt.started_at, attempt.submitted_at),
            "violation_count": attempt.violation_count,
            "status": attempt.status.value if hasattr(attempt.status, "value") else str(attempt.status),
        })

    # 3. Topic Mastery Breakdown (Tỷ lệ đúng/sai theo chuyên đề)
    attempt_ids = [a.id for a in attempts]
    topic_stats: Dict[str, Dict[str, Any]] = {}

    if attempt_ids:
        answers = (
            db.query(AttemptAnswer)
            .options(
                joinedload(AttemptAnswer.question).joinedload(Question.category)
            )
            .filter(AttemptAnswer.attempt_id.in_(attempt_ids))
            .all()
        )

        for ans in answers:
            q = ans.question
            cat = q.category if q else None
            cat_id = str(cat.id) if cat else "uncategorized"
            cat_name = cat.name if cat else "Kiến thức chung"

            if cat_id not in topic_stats:
                topic_stats[cat_id] = {
                    "category_id": cat_id if cat_id != "uncategorized" else None,
                    "category_name": cat_name,
                    "total_questions": 0,
                    "correct_count": 0,
                    "incorrect_count": 0,
                }

            topic_stats[cat_id]["total_questions"] += 1
            if ans.is_correct:
                topic_stats[cat_id]["correct_count"] += 1
            else:
                topic_stats[cat_id]["incorrect_count"] += 1

    topics_mastery = []
    knowledge_gaps = []

    for cat_data in topic_stats.values():
        total = cat_data["total_questions"]
        correct = cat_data["correct_count"]
        incorrect = cat_data["incorrect_count"]
        acc = round((correct / total) * 100, 1) if total > 0 else 0.0

        if acc >= 85:
            mastery_level = "EXCELLENT"
        elif acc >= 70:
            mastery_level = "GOOD"
        elif acc >= 50:
            mastery_level = "AVERAGE"
        else:
            mastery_level = "NEEDS_IMPROVEMENT"

        item = {
            "category_id": cat_data["category_id"],
            "category_name": cat_data["category_name"],
            "total_questions": total,
            "correct_count": correct,
            "incorrect_count": incorrect,
            "accuracy_percentage": acc,
            "mastery_level": mastery_level,
        }
        topics_mastery.append(item)

        # Flag knowledge gaps if accuracy < 65% and at least 1 wrong answer
        if acc < 65 and incorrect > 0:
            knowledge_gaps.append({
                "category_name": cat_data["category_name"],
                "incorrect_count": incorrect,
                "accuracy_percentage": acc,
                "advice": (
                    f"Cần ôn tập lại các khái niệm trọng tâm trong '{cat_data['category_name']}' "
                    f"(tỷ lệ chính xác hiện tại là {acc}%, sai {incorrect}/{total} câu)."
                ),
            })

    # Sort topics by accuracy descending
    topics_mastery.sort(key=lambda x: x["accuracy_percentage"], reverse=True)
    knowledge_gaps.sort(key=lambda x: x["accuracy_percentage"])

    return {
        "student_id": str(student.id),
        "student_name": student.full_name,
        "student_email": student.email,
        "summary": summary,
        "trends": trends,
        "topics_mastery": topics_mastery,
        "knowledge_gaps": knowledge_gaps,
    }


def get_exam_distribution_analytics(
    db: Session,
    exam_id: uuid.UUID,
    current_user: Optional[User] = None,
) -> Dict[str, Any]:
    """Calculate score distribution histogram, exam statistics, top difficult questions,

    and student score sheet for an exam (WBS 5.3.2).

    RBAC:
    - STUDENT: forbidden (403).
    - INSTRUCTOR: must be the creator of the exam (exam.instructor_id == current_user.id).
    - ADMIN: allowed to view any exam.
    """
    exam = (
        db.query(Exam)
        .options(
            joinedload(Exam.instructor),
            joinedload(Exam.exam_questions).joinedload(ExamQuestion.question).joinedload(Question.category),
        )
        .filter(Exam.id == exam_id)
        .first()
    )
    if not exam:
        raise NotFoundError(f"Đề thi với ID '{exam_id}' không tồn tại.")

    # Authorization Check
    if current_user:
        if current_user.role == UserRole.STUDENT:
            raise PermissionError("Sinh viên không có quyền xem thống kê phân tích đề thi và phổ điểm lớp học.")
        if current_user.role == UserRole.INSTRUCTOR and exam.instructor_id != current_user.id:
            raise PermissionError("Bạn chỉ có quyền xem thống kê của các đề thi do chính mình tạo.")

    # Query completed attempts for this exam
    attempts = (
        db.query(ExamAttempt)
        .options(joinedload(ExamAttempt.student))
        .filter(
            ExamAttempt.exam_id == exam_id,
            ExamAttempt.status != AttemptStatus.IN_PROGRESS,
            ExamAttempt.score.isnot(None),
        )
        .order_by(ExamAttempt.score.desc(), ExamAttempt.submitted_at.desc())
        .all()
    )

    total_attempts = len(attempts)
    unique_students = set(a.student_id for a in attempts)
    total_questions = len(exam.exam_questions) if exam.exam_questions else 0

    scores = [a.score for a in attempts if a.score is not None]

    if total_attempts > 0:
        min_score = round(min(scores), 2)
        max_score = round(max(scores), 2)
        avg_score = round(sum(scores) / total_attempts, 2)
        median_score = _compute_median(scores)
        pass_count = sum(1 for s in scores if s >= 5.0)
        fail_count = sum(1 for s in scores if s < 5.0)
        pass_rate = round((pass_count / total_attempts) * 100, 1)
        std_dev = _compute_std_dev(scores, avg_score)
    else:
        min_score = 0.0
        max_score = 0.0
        avg_score = 0.0
        median_score = 0.0
        pass_count = 0
        fail_count = 0
        pass_rate = 0.0
        std_dev = 0.0

    summary = {
        "total_attempts": total_attempts,
        "total_students": len(unique_students),
        "min_score": min_score,
        "max_score": max_score,
        "avg_score": avg_score,
        "median_score": median_score,
        "pass_count": pass_count,
        "fail_count": fail_count,
        "pass_rate": pass_rate,
        "standard_deviation": std_dev,
    }

    # 1. 10-Bin Score Histogram (0-1, 1-2, ..., 9-10)
    # Bins: [0, 1), [1, 2), ..., [9, 10]
    hist_bins = [
        {"bin_label": f"{i} - <{i+1}" if i < 9 else "9 - 10", "min_score": float(i), "max_score": float(i+1), "count": 0, "percentage": 0.0}
        for i in range(10)
    ]
    for s in scores:
        idx = min(9, int(s)) if s < 10.0 else 9
        hist_bins[idx]["count"] += 1

    for b in hist_bins:
        b["percentage"] = round((b["count"] / total_attempts) * 100, 1) if total_attempts > 0 else 0.0

    # 2. Academic Grade Distribution (Thang phân loại học lực)
    # Xuất sắc: 9.0 - 10.0
    # Giỏi: 8.0 - <9.0
    # Khá: 6.5 - <8.0
    # Trung bình: 5.0 - <6.5
    # Yếu / Kém: <5.0
    grade_tiers = [
        {"bin_label": "Xuất sắc (9.0 - 10.0)", "min_score": 9.0, "max_score": 10.0, "count": 0, "percentage": 0.0},
        {"bin_label": "Giỏi (8.0 - <9.0)", "min_score": 8.0, "max_score": 9.0, "count": 0, "percentage": 0.0},
        {"bin_label": "Khá (6.5 - <8.0)", "min_score": 6.5, "max_score": 8.0, "count": 0, "percentage": 0.0},
        {"bin_label": "Trung bình (5.0 - <6.5)", "min_score": 5.0, "max_score": 6.5, "count": 0, "percentage": 0.0},
        {"bin_label": "Yếu / Kém (<5.0)", "min_score": 0.0, "max_score": 5.0, "count": 0, "percentage": 0.0},
    ]

    for s in scores:
        if s >= 9.0:
            grade_tiers[0]["count"] += 1
        elif s >= 8.0:
            grade_tiers[1]["count"] += 1
        elif s >= 6.5:
            grade_tiers[2]["count"] += 1
        elif s >= 5.0:
            grade_tiers[3]["count"] += 1
        else:
            grade_tiers[4]["count"] += 1

    for gt in grade_tiers:
        gt["percentage"] = round((gt["count"] / total_attempts) * 100, 1) if total_attempts > 0 else 0.0

    # 3. Top Most Frequently Missed Questions (Top câu hỏi hay sai nhất)
    difficult_questions = []
    attempt_ids = [a.id for a in attempts]

    if attempt_ids:
        answers = (
            db.query(AttemptAnswer)
            .options(
                joinedload(AttemptAnswer.question).joinedload(Question.category)
            )
            .filter(AttemptAnswer.attempt_id.in_(attempt_ids))
            .all()
        )

        question_stats: Dict[uuid.UUID, Dict[str, Any]] = {}
        for ans in answers:
            qid = ans.question_id
            if qid not in question_stats:
                q = ans.question
                cat_name = q.category.name if q and q.category else "Chung"
                q_content = q.content if q else "Câu hỏi"
                q_type = q.question_type.value if q and hasattr(q.question_type, "value") else str(getattr(q, "question_type", ""))
                question_stats[qid] = {
                    "question_id": str(qid),
                    "content": q_content,
                    "question_type": q_type,
                    "category_name": cat_name,
                    "total_responses": 0,
                    "wrong_count": 0,
                    "correct_count": 0,
                }

            question_stats[qid]["total_responses"] += 1
            if ans.is_correct:
                question_stats[qid]["correct_count"] += 1
            else:
                question_stats[qid]["wrong_count"] += 1

        for stat in question_stats.values():
            tot = stat["total_responses"]
            wrong = stat["wrong_count"]
            stat["incorrect_rate"] = round((wrong / tot) * 100, 1) if tot > 0 else 0.0
            difficult_questions.append(stat)

        # Sort by wrong_count desc, incorrect_rate desc
        difficult_questions.sort(key=lambda x: (x["wrong_count"], x["incorrect_rate"]), reverse=True)
        # Limit to top 5
        difficult_questions = difficult_questions[:5]

    # 4. Student Score Sheet (Bảng điểm danh sách phục vụ xem & xuất CSV)
    student_scores = []
    for a in attempts:
        student_scores.append({
            "student_id": str(a.student_id),
            "student_name": a.student.full_name if a.student else "Chưa rõ",
            "student_email": a.student.email if a.student else "Chưa rõ",
            "attempt_id": str(a.id),
            "attempt_number": a.attempt_number,
            "score": round(a.score, 2) if a.score is not None else 0.0,
            "submitted_at": a.submitted_at.isoformat() if a.submitted_at else None,
            "time_spent_seconds": _calculate_time_spent(a.started_at, a.submitted_at),
            "violation_count": a.violation_count,
            "status": a.status.value if hasattr(a.status, "value") else str(a.status),
        })

    return {
        "exam_id": str(exam.id),
        "exam_code": exam.exam_code,
        "exam_title": exam.title,
        "duration_minutes": exam.duration_minutes,
        "total_questions": total_questions,
        "summary": summary,
        "score_distribution": hist_bins,
        "grade_distribution": grade_tiers,
        "difficult_questions": difficult_questions,
        "student_scores": student_scores,
    }


def list_accessible_exams_for_instructor(
    db: Session,
    current_user: User,
) -> List[Dict[str, Any]]:
    """List exams accessible to current instructor or admin for dropdown selector."""
    query = db.query(Exam)
    if current_user.role == UserRole.INSTRUCTOR:
        query = query.filter(Exam.instructor_id == current_user.id)
    elif current_user.role != UserRole.ADMIN:
        # Students shouldn't list exams via this instructor endpoint
        return []

    exams = query.order_by(Exam.created_at.desc()).all()
    results = []
    for e in exams:
        results.append({
            "id": str(e.id),
            "exam_code": e.exam_code,
            "title": e.title,
            "duration_minutes": e.duration_minutes,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        })
    return results
