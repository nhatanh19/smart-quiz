"""Deterministic display ordering; original question and option IDs never change."""

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
    raise NotImplementedError
