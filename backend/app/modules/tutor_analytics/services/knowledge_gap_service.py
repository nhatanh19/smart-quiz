"""Service for Knowledge Gap Diagnosis & Actionable Study Advice (Issue #17, WBS 5.2.2)."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid
from sqlalchemy.orm import Session, joinedload

from app.models.entities import (
    AttemptAnswer,
    AttemptStatus,
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


def diagnose_knowledge_gaps(
    db: Session,
    attempt_id: uuid.UUID,
    current_user: Optional[User] = None,
) -> Dict[str, Any]:
    """Diagnose student knowledge gaps and generate actionable study advice.

    Fulfills Issue #17 Acceptance Criteria:
    - Analyzes student answers, groups wrong questions by topic/tags.
    - Explicitly surfaces: "Chủ đề bạn cần củng cố: <Tên chủ đề>"
    - Recommends at least 2 concrete study suggestions to improve outcomes.
    """
    attempt = (
        db.query(ExamAttempt)
        .options(joinedload(ExamAttempt.student), joinedload(ExamAttempt.exam))
        .filter(ExamAttempt.id == attempt_id)
        .first()
    )
    if not attempt:
        raise NotFoundError(f"Exam attempt with id '{attempt_id}' not found.")

    if current_user:
        if current_user.role == UserRole.STUDENT and attempt.student_id != current_user.id:
            raise PermissionError("Bạn không có quyền xem chẩn đoán lỗ hổng kiến thức của thí sinh khác.")

    if attempt.status == AttemptStatus.IN_PROGRESS:
        raise InvalidAttemptStateError("Bài thi đang trong thời gian làm và chưa được nộp.")

    # 1. Fetch submitted answers
    answers = (
        db.query(AttemptAnswer)
        .filter(AttemptAnswer.attempt_id == attempt_id)
        .all()
    )
    answers_by_qid = {ans.question_id: ans for ans in answers}

    # 2. Collect questions (from snapshot or exam questions)
    questions_list: List[Question] = []
    snapshot = attempt.question_order_snapshot

    if snapshot and isinstance(snapshot, dict) and bool(snapshot.get("questions")):
        for item in snapshot["questions"]:
            try:
                raw_qid = item.get("question_id")
                q_id = uuid.UUID(str(raw_qid)) if raw_qid else None
            except Exception:
                continue
            if not q_id:
                continue
            q = (
                db.query(Question)
                .options(joinedload(Question.category))
                .filter(Question.id == q_id)
                .first()
            )
            if q:
                questions_list.append(q)
    else:
        eq_list = (
            db.query(ExamQuestion)
            .options(joinedload(ExamQuestion.question).joinedload(Question.category))
            .filter(ExamQuestion.exam_id == attempt.exam_id)
            .order_by(ExamQuestion.order_index.asc())
            .all()
        )
        for eq in eq_list:
            if eq.question:
                questions_list.append(eq.question)

    if not questions_list and answers:
        for ans in answers:
            q = (
                db.query(Question)
                .options(joinedload(Question.category))
                .filter(Question.id == ans.question_id)
                .first()
            )
            if q:
                questions_list.append(q)

    # 3. Aggregate statistics by topic/tags
    # Each question may have:
    # - `tags`: JSONB array of string tags (e.g. ["Kế thừa & Đa hình trong OOP", "Encapsulation"])
    # - `category`: Category object with `name`
    topic_map: Dict[str, Dict[str, Any]] = {}
    total_wrong = 0
    total_questions = len(questions_list)

    for q in questions_list:
        ans = answers_by_qid.get(q.id)
        is_correct = bool(ans.is_correct) if (ans and ans.is_correct is not None) else False
        if not is_correct:
            total_wrong += 1

        # Extract topics for this question
        topics: List[str] = []
        if isinstance(q.tags, list) and q.tags:
            topics.extend([str(t).strip() for t in q.tags if str(t).strip()])
        if not topics and q.category and q.category.name:
            topics.append(q.category.name.strip())
        if not topics:
            topics.append("Kiến thức tổng quát")

        for t in topics:
            if t not in topic_map:
                topic_map[t] = {
                    "topic": t,
                    "total_questions": 0,
                    "wrong_count": 0,
                    "question_ids": [],
                    "cognitive_levels": set(),
                }
            topic_map[t]["total_questions"] += 1
            topic_map[t]["question_ids"].append(str(q.id))
            if hasattr(q.cognitive_level, "value"):
                topic_map[t]["cognitive_levels"].add(q.cognitive_level.value)
            elif q.cognitive_level:
                topic_map[t]["cognitive_levels"].add(str(q.cognitive_level))

            if not is_correct:
                topic_map[t]["wrong_count"] += 1

    # 4. Formulate weak topics
    weak_topics_list: List[Dict[str, Any]] = []
    for t_name, stat in topic_map.items():
        total_q = stat["total_questions"]
        wrong_q = stat["wrong_count"]
        acc_pct = round(((total_q - wrong_q) / total_q) * 100, 1) if total_q > 0 else 0.0
        if wrong_q > 0:
            weak_topics_list.append({
                "topic": t_name,
                "wrong_count": wrong_q,
                "total_questions": total_q,
                "accuracy_percentage": acc_pct,
                "question_ids": stat["question_ids"],
                "cognitive_levels": list(stat["cognitive_levels"]),
            })

    # Sort weak topics: highest mistakes first, then lowest accuracy
    weak_topics_list.sort(key=lambda item: (-item["wrong_count"], item["accuracy_percentage"]))

    has_gaps = len(weak_topics_list) > 0
    advice_list: List[Dict[str, Any]] = []

    if has_gaps:
        primary_weak_topic = weak_topics_list[0]["topic"]
        summary_headline = f"Chủ đề bạn cần củng cố: {primary_weak_topic}"

        # Generate Actionable Study Advice (Minimum 2 concrete recommendations)
        # 1. Core theory reinforcement
        advice_list.append({
            "title": "Củng cố lý thuyết & nguyên lý cốt lõi",
            "description": f"Đọc lại tài liệu, slide bài giảng về chủ đề '{primary_weak_topic}'. Chú trọng nắm vững định nghĩa, cơ chế hoạt động và phân biệt rõ các khái niệm dễ gây nhầm lẫn.",
            "action_type": "REVIEW_THEORY",
            "priority": "HIGH",
            "resource_hint": f"Tài liệu chuyên đề: {primary_weak_topic}",
        })

        # 2. Targeted practice questions
        advice_list.append({
            "title": "Luyện tập bài tập chuyên sâu",
            "description": f"Thực hành thêm 5–10 câu hỏi trắc nghiệm chuyên sâu về '{primary_weak_topic}' ở mức độ vận dụng (Apply) để rèn luyện phản xạ và nhận diện bẫy đề thi.",
            "action_type": "PRACTICE_QUIZ",
            "priority": "HIGH",
            "resource_hint": f"Ngân hàng đề câu hỏi mức độ Vận dụng: {primary_weak_topic}",
        })

        # 3. AI Tutor interaction recommendation
        advice_list.append({
            "title": "Đối chiếu nguyên nhân sai cùng Gia sư ảo AI",
            "description": "Bấm nút 'Giải thích bằng AI' trên từng câu hỏi làm sai ở màn hình xem lại để nghe AI Tutor phân tích tại sao phương án bạn chọn là sai.",
            "action_type": "AI_TUTOR_REVIEW",
            "priority": "MEDIUM",
            "resource_hint": "Tính năng Giải thích ngữ cảnh AI Tutor",
        })
    else:
        primary_weak_topic = None
        summary_headline = "Xuất sắc! Bạn không có lỗ hổng kiến thức nào trong bài thi này."
        advice_list.append({
            "title": "Mở rộng kiến thức nâng cao",
            "description": "Bạn đã nắm rất vững toàn bộ nội dung trong bài kiểm tra. Hãy tìm hiểu thêm các tình huống kiến trúc và bài toán tối ưu hoá thực tế.",
            "action_type": "ADVANCED_STUDY",
            "priority": "MEDIUM",
            "resource_hint": "Tài liệu nâng cao & Best Practices",
        })
        advice_list.append({
            "title": "Hỗ trợ học tập cùng nhóm",
            "description": "Tham gia trao đổi, thảo luận giải thích cho các bạn trong lớp để khắc sâu tư duy phản biện và khả năng truyền đạt kiến thức.",
            "action_type": "PEER_LEARNING",
            "priority": "MEDIUM",
            "resource_hint": "Cộng đồng học tập Smart Quiz",
        })

    # Sanitize cognitive levels to avoid returning sets
    for item in weak_topics_list:
        if "cognitive_levels" in item and isinstance(item["cognitive_levels"], set):
            item["cognitive_levels"] = list(item["cognitive_levels"])

    return {
        "attempt_id": str(attempt.id),
        "exam_id": str(attempt.exam_id),
        "summary_headline": summary_headline,
        "primary_weak_topic": primary_weak_topic,
        "has_gaps": has_gaps,
        "total_wrong": total_wrong,
        "total_questions": total_questions,
        "weak_topics": weak_topics_list,
        "advice": advice_list,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
