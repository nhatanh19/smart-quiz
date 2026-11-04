"""Pydantic schemas for the Auto-Grading Engine and Tutor Analytics module."""

import uuid
from typing import List
from pydantic import BaseModel, ConfigDict


class AnswerGradingSchema(BaseModel):
    """Grading detail for a single question."""
    question_id: uuid.UUID
    is_correct: bool
    points_awarded: float

    model_config = ConfigDict(from_attributes=True)


class GradingResultSchema(BaseModel):
    """Overall grading result for an exam attempt."""
    attempt_id: uuid.UUID
    score: float
    correct_count: int
    total_questions: int
    answers: List[AnswerGradingSchema]
    time_spent_seconds: int
    already_graded: bool = False

    model_config = ConfigDict(from_attributes=True)
