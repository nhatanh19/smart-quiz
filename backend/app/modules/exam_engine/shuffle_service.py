"""Deterministic display ordering; original question and option IDs never change."""

import hashlib
import json
import random
import uuid

from app.models.entities import ExamQuestion


def build_attempt_snapshot(
    exam_questions: list[ExamQuestion],
    student_id: uuid.UUID,
    exam_id: uuid.UUID,
    attempt_number: int,
    *,
    shuffle_questions: bool = True,
    shuffle_options: bool = True,
) -> dict:
    """Return DATABASE_GUIDE section 5.3's version-1 snapshot.

    Input relationships must be loaded, belong to exam_id, and have unique
    question IDs, order indexes and option IDs. Original order is order_index
    for questions and the questions.options array order for options.

    The seed includes student_id, exam_id and attempt_number. Neither input
    objects nor global random state are modified. Persist the returned snapshot
    once per attempt and reuse it on reload; do not regenerate a saved attempt.
    selected_options must always contain original option IDs (K-01), and submit
    must reject question IDs outside this snapshot (K-02).

    Raise ValueError for invalid source data or an attempt number below one.
    """
    if type(attempt_number) is not int or attempt_number < 1:
        raise ValueError("attempt_number must be a positive integer")
    ordered = sorted(exam_questions, key=lambda item: item.order_index)
    question_ids = [str(item.question_id) for item in ordered]
    indexes = [item.order_index for item in ordered]
    if len(set(question_ids)) != len(ordered) or len(set(indexes)) != len(ordered):
        raise ValueError("Duplicate question ID or order index")
    for item in ordered:
        if item.exam_id != exam_id or item.question.id != item.question_id:
            raise ValueError("Question does not belong to the requested exam")
        if item.order_index < 1:
            raise ValueError("order_index must be positive")
        options = item.question.options
        if not isinstance(options, list) or not 2 <= len(options) <= 10:
            raise ValueError("A question must have 2 to 10 options")
        ids = [option.get("id") if isinstance(option, dict) else None for option in options]
        if any(not isinstance(key, str) or not key.isalpha() or not key.isupper() for key in ids):
            raise ValueError("Option IDs must be uppercase letters")
        if len(set(ids)) != len(ids):
            raise ValueError("Duplicate option ID")

    seed = (str(student_id), str(exam_id), attempt_number)
    if shuffle_questions:
        _shuffle(ordered, _rng(*seed, "questions"))
    questions = []
    for item in ordered:
        option_ids = [option["id"] for option in item.question.options]
        if shuffle_options:
            _shuffle(option_ids, _rng(*seed, "options", str(item.question_id)))
        questions.append({"question_id": str(item.question_id), "options_order": option_ids})
    return {"version": 1, "questions": questions}


def _rng(*parts: object) -> random.Random:
    encoded = json.dumps(parts, separators=(",", ":")).encode("utf-8")
    return random.Random(int.from_bytes(hashlib.sha256(encoded).digest(), "big"))


def _shuffle(items: list, rng: random.Random) -> None:
    """In-place Fisher-Yates on a private list; O(n) time."""
    for index in range(len(items) - 1, 0, -1):
        other = rng.randrange(index + 1)
        items[index], items[other] = items[other], items[index]


def render_attempt_questions(snapshot: dict, exam_questions: list[ExamQuestion]) -> list[dict]:
    """Render saved ordering using original IDs, without exposing answer keys.

    Source questions must not change after an attempt starts (DB spec section 8).
    Raise ValueError on a stale/invalid snapshot rather than silently reshuffling.
    """
    rows = _snapshot_rows(snapshot)
    by_id = {str(item.question_id): item.question for item in exam_questions}
    result = []
    for row in rows:
        question = by_id.get(row["question_id"])
        if question is None:
            raise ValueError("Snapshot question is missing from the exam")
        options = {option["id"]: option for option in question.options}
        if set(row["options_order"]) != set(options):
            raise ValueError("Snapshot options do not match the question")
        result.append({
            "question_id": row["question_id"],
            "content": question.content,
            "question_type": question.question_type.value,
            "options": [{"id": key, "text": options[key]["text"]} for key in row["options_order"]],
        })
    return result


def validate_attempt_answers(snapshot: dict, answers: list[dict]) -> None:
    """Validate K-01/K-02 before any writes; IDs are never display positions.

    A missing answer or [] means unanswered. Reject duplicate question/option
    IDs and IDs not present in the saved snapshot. The caller handles ownership,
    timing, question-type cardinality and transaction management.
    """
    allowed = {row["question_id"]: set(row["options_order"]) for row in _snapshot_rows(snapshot)}
    seen = set()
    for answer in answers:
        question_id = str(answer["question_id"])
        if question_id not in allowed or question_id in seen:
            raise ValueError("Question is outside the snapshot or duplicated")
        selected = answer["selected_options"]
        if not isinstance(selected, list) or any(not isinstance(key, str) for key in selected):
            raise ValueError("selected_options must be a list of original option IDs")
        if len(selected) != len(set(selected)) or not set(selected) <= allowed[question_id]:
            raise ValueError("Invalid or duplicate original option ID")
        seen.add(question_id)


def _snapshot_rows(snapshot: dict) -> list[dict]:
    if snapshot.get("version") != 1 or not isinstance(snapshot.get("questions"), list):
        raise ValueError("Unsupported snapshot schema")
    seen = set()
    for row in snapshot["questions"]:
        if not isinstance(row, dict) or not isinstance(row.get("question_id"), str):
            raise ValueError("Invalid snapshot question")
        ids = row.get("options_order")
        if not isinstance(ids, list) or any(not isinstance(key, str) for key in ids):
            raise ValueError("Invalid snapshot option IDs")
        if row["question_id"] in seen or len(ids) != len(set(ids)):
            raise ValueError("Duplicate snapshot question or option")
        seen.add(row["question_id"])
    return snapshot["questions"]
