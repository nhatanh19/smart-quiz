"""Instant Multi-Question Type Auto-Grading Engine.

Implements DEV3_DEV4_WORKING_AGREEMENT.md section 7 and DATABASE_GUIDE.md.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
import logging
from typing import List, Optional
import uuid

from sqlalchemy.orm import Session, joinedload

from app.models.entities import (
    AttemptAnswer,
    AttemptStatus,
    ExamAttempt,
    ExamQuestion,
    QuestionType,
)
from app.modules.tutor_analytics.exceptions import (
    InvalidAttemptStateError,
    NotFoundError,
    SnapshotMismatchError,
)

logger = logging.getLogger(__name__)


@dataclass
class GradingResult:
    """Standardized grading result returned to callers."""
    attempt_id: uuid.UUID
    score: float
    correct_count: int
    total_questions: int
    answers: list[dict]  # [{question_id, is_correct, points_awarded}]
    time_spent_seconds: int
    already_graded: bool = False


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


def grade_attempt(
    db: Session,
    attempt_id: uuid.UUID,
    *,
    force: bool = False,
) -> GradingResult:
    """Synchronous auto-grading engine.
    
    Grading formula:
    - SINGLE_CHOICE: ratio = 1.0 if S == C and len(S) == 1 else 0.0
    - TRUE_FALSE: ratio = 1.0 if S == C and len(S) == 1 else 0.0
    - MULTIPLE_CHOICE: ratio = clamp((|S ∩ C| - |S \\ C|) / |C|, 0, 1)
    - Unanswered / Empty S = []: ratio = 0.0, is_correct = False
    
    Rules & Constraints:
    - points_awarded = round(exam_questions.points * ratio, 2)
    - score = clamp(round(Σ points_awarded / Σ exam_questions.points * 10, 2), 0, 10)
    - I-01: ONLY flushes changes to session; caller MUST commit.
    - K-01: selected_options contains original option IDs.
    - K-02: question_id must belong to attempt snapshot.
    
    Raises:
        NotFoundError: if attempt_id is not found.
        InvalidAttemptStateError: if attempt state or snapshot is malformed.
        SnapshotMismatchError: if an answer refers to a question not in the snapshot.
    """
    if isinstance(attempt_id, str):
        try:
            attempt_id = uuid.UUID(attempt_id)
        except ValueError:
            raise NotFoundError(f"Invalid attempt UUID: {attempt_id}")

    attempt = (
        db.query(ExamAttempt)
        .filter(ExamAttempt.id == attempt_id)
        .first()
    )
    if not attempt:
        raise NotFoundError(f"Exam attempt '{attempt_id}' not found.")

    snapshot = attempt.question_order_snapshot
    if not isinstance(snapshot, dict) or snapshot.get("version") != 1 or not isinstance(snapshot.get("questions"), list):
        raise InvalidAttemptStateError("Attempt question_order_snapshot is missing or unsupported.")

    snapshot_rows = snapshot["questions"]
    snapshot_qids = {
        str(row["question_id"])
        for row in snapshot_rows
        if isinstance(row, dict) and "question_id" in row
    }

    # E2: Attempt already SUBMITTED and force=False -> return cached result without overwriting
    if attempt.status == AttemptStatus.SUBMITTED and not force:
        existing_answers = (
            db.query(AttemptAnswer)
            .filter(AttemptAnswer.attempt_id == attempt.id)
            .all()
        )
        ans_map = {str(a.question_id): a for a in existing_answers}
        summary_answers = []
        for row in snapshot_rows:
            qid_str = str(row["question_id"])
            ans = ans_map.get(qid_str)
            summary_answers.append({
                "question_id": qid_str,
                "is_correct": bool(ans.is_correct) if ans and ans.is_correct is not None else False,
                "points_awarded": float(ans.points_awarded) if ans and ans.points_awarded is not None else 0.0,
            })
        return GradingResult(
            attempt_id=attempt.id,
            score=float(attempt.score) if attempt.score is not None else 0.0,
            correct_count=sum(1 for a in summary_answers if a["is_correct"]),
            total_questions=len(snapshot_rows),
            answers=summary_answers,
            time_spent_seconds=_calculate_time_spent(attempt.started_at, attempt.submitted_at),
            already_graded=True,
        )

    # 1 query for exam questions with joined questions (No N+1)
    exam_questions = (
        db.query(ExamQuestion)
        .options(joinedload(ExamQuestion.question))
        .filter(ExamQuestion.exam_id == attempt.exam_id)
        .all()
    )
    eq_map = {str(eq.question_id): eq for eq in exam_questions}

    # 1 query for attempt answers
    attempt_answers = (
        db.query(AttemptAnswer)
        .filter(AttemptAnswer.attempt_id == attempt.id)
        .all()
    )

    # E4 / K-02: Every answered question_id MUST belong to snapshot
    for ans in attempt_answers:
        if str(ans.question_id) not in snapshot_qids:
            raise SnapshotMismatchError(
                f"Question ID '{ans.question_id}' in answers does not belong to attempt snapshot."
            )

    ans_by_qid = {str(ans.question_id): ans for ans in attempt_answers}

    summary_answers = []
    total_awarded_points = 0.0

    # Grade each question in snapshot order
    for row in snapshot_rows:
        qid_str = str(row["question_id"])
        eq = eq_map.get(qid_str)
        if not eq or not eq.question:
            raise InvalidAttemptStateError(
                f"Snapshot question '{qid_str}' not found in exam questions configuration."
            )
        question = eq.question
        ans = ans_by_qid.get(qid_str)

        # E7: Question without record in attempt_answers -> award 0 points, create answer record
        if ans is None:
            ans = AttemptAnswer(
                attempt_id=attempt.id,
                question_id=eq.question_id,
                selected_options=[],
                is_correct=False,
                points_awarded=0.0,
            )
            db.add(ans)
            ans_by_qid[qid_str] = ans

        raw_selected = ans.selected_options if isinstance(ans.selected_options, list) else []
        # E6: Deduplicate selected_options preserving order
        seen_opts = set()
        deduped_selected = []
        for opt_id in raw_selected:
            if isinstance(opt_id, str) and opt_id not in seen_opts:
                seen_opts.add(opt_id)
                deduped_selected.append(opt_id)

        S = set(deduped_selected)
        opts = question.options if isinstance(question.options, list) else []
        valid_opts = {opt.get("id") for opt in opts if isinstance(opt, dict) and "id" in opt}
        C = {opt.get("id") for opt in opts if isinstance(opt, dict) and opt.get("is_correct") is True}

        # E5: selected_options contains option id not in question -> treated as wrong, log warning
        if not S.issubset(valid_opts):
            logger.warning(
                "Question %s answer contains unknown option IDs: %s",
                qid_str,
                S - valid_opts,
            )
            ratio = 0.0
            is_correct = False
        elif len(S) == 0:
            ratio = 0.0
            is_correct = False
        elif question.question_type in (QuestionType.SINGLE_CHOICE, QuestionType.TRUE_FALSE):
            if len(S) == 1 and S == C:
                ratio = 1.0
                is_correct = True
            else:
                ratio = 0.0
                is_correct = False
        elif question.question_type == QuestionType.MULTIPLE_CHOICE:
            if len(C) == 0:
                ratio = 0.0
                is_correct = False
            else:
                correct_selected = len(S.intersection(C))
                wrong_selected = len(S.difference(C))
                raw_ratio = (correct_selected - wrong_selected) / len(C)
                ratio = max(0.0, min(1.0, raw_ratio))
                is_correct = (S == C)
        else:
            ratio = 0.0
            is_correct = False

        q_max_points = eq.points if eq.points is not None else 1.0
        points_awarded = round(q_max_points * ratio, 2)

        ans.is_correct = is_correct
        ans.points_awarded = points_awarded

        total_awarded_points += points_awarded
        summary_answers.append({
            "question_id": qid_str,
            "is_correct": is_correct,
            "points_awarded": points_awarded,
        })

    # E8: 0 questions / total points = 0 -> score = 0.0
    total_exam_points = sum(eq.points for eq in exam_questions if eq.points is not None)
    if total_exam_points <= 0 or len(snapshot_rows) == 0:
        logger.warning("Total exam points for exam %s is <= 0; final score set to 0.0", attempt.exam_id)
        final_score = 0.0
    else:
        raw_score = (total_awarded_points / total_exam_points) * 10.0
        final_score = max(0.0, min(10.0, round(raw_score, 2)))  # E9: Clamp [0, 10]

    now = datetime.now(timezone.utc)
    if attempt.status == AttemptStatus.IN_PROGRESS:
        attempt.status = AttemptStatus.SUBMITTED
        if attempt.submitted_at is None:
            attempt.submitted_at = now
    elif attempt.status in (AttemptStatus.LOCKED_VIOLATION, AttemptStatus.EXPIRED):
        # E3: keep status, set submitted_at if not set
        if attempt.submitted_at is None:
            attempt.submitted_at = now
    elif attempt.status == AttemptStatus.SUBMITTED:
        if attempt.submitted_at is None:
            attempt.submitted_at = now

    attempt.score = final_score

    # I-01: NO COMMIT, ONLY FLUSH
    db.flush()

    time_spent = _calculate_time_spent(attempt.started_at, attempt.submitted_at)
    correct_count = sum(1 for a in summary_answers if a["is_correct"])

    return GradingResult(
        attempt_id=attempt.id,
        score=final_score,
        correct_count=correct_count,
        total_questions=len(snapshot_rows),
        answers=summary_answers,
        time_spent_seconds=time_spent,
        already_graded=False,
    )
