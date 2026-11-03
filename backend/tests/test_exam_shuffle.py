"""Issue #13: real ORM inputs; no database needed for the pure shuffle service."""
import copy
import json
import os
from pathlib import Path
import random
import subprocess
import sys
from uuid import UUID

import pytest

from app.models.entities import ExamQuestion, Question, QuestionType
from app.modules.exam_engine.shuffle_service import (
    build_attempt_snapshot, render_attempt_questions, validate_attempt_answers,
)

EXAM = UUID(int=100)
STUDENT = UUID(int=200)


def make_questions():
    return [ExamQuestion(
        exam_id=EXAM, question_id=UUID(int=index), order_index=index,
        question=Question(
            id=UUID(int=index), content=f"Question {index}",
            question_type=QuestionType.SINGLE_CHOICE,
            explanation="Private explanation",
            options=[{"id": key, "text": f"Option {key}", "is_correct": key == "A"}
                     for key in "ABCD"],
        ),
    ) for index in range(1, 9)]


def snapshot(questions, **kwargs):
    return build_attempt_snapshot(questions, STUDENT, EXAM, 1, **kwargs)


def test_deterministic_canonical_input_and_no_mutation():
    questions = make_questions()
    original = copy.deepcopy([item.question.options for item in questions])
    state = random.getstate()
    result = snapshot(questions)
    assert result == snapshot(list(reversed(questions)))
    assert random.getstate() == state
    assert [item.order_index for item in questions] == list(range(1, 9))
    assert [item.question.options for item in questions] == original
    assert set(row["question_id"] for row in result["questions"]) == {str(item.question_id) for item in questions}
    assert all(sorted(row["options_order"]) == list("ABCD") for row in result["questions"])


def test_different_students_and_attempts():
    questions = make_questions()
    first = snapshot(questions)
    second = build_attempt_snapshot(questions, UUID(int=201), EXAM, 1)
    assert [row["question_id"] for row in first["questions"]] != [row["question_id"] for row in second["questions"]]
    orders = lambda value: {row["question_id"]: row["options_order"] for row in value["questions"]}
    assert orders(first) != orders(second)
    assert first != build_attempt_snapshot(questions, STUDENT, EXAM, 2)


@pytest.mark.parametrize("shuffle_questions,shuffle_options", [(False, False), (False, True), (True, False), (True, True)])
def test_flags_are_independent(shuffle_questions, shuffle_options):
    questions = make_questions()
    result = snapshot(questions, shuffle_questions=shuffle_questions, shuffle_options=shuffle_options)
    if not shuffle_questions:
        assert [row["question_id"] for row in result["questions"]] == [str(item.question_id) for item in questions]
    baseline = {row["question_id"]: row["options_order"] for row in snapshot(questions)["questions"]}
    for row in result["questions"]:
        assert row["options_order"] == (baseline[row["question_id"]] if shuffle_options else list("ABCD"))


def test_restart_with_different_python_hash_seeds():
    script = """from test_exam_shuffle import make_questions, snapshot
import json
print(json.dumps(snapshot(make_questions()), sort_keys=True))
"""
    root = Path(__file__).resolve().parents[1]
    results = []
    for seed in ("1", "987"):
        env = dict(os.environ, PYTHONHASHSEED=seed, DATABASE_URL="sqlite://",
                   PYTHONPATH=os.pathsep.join((str(root), str(root / "tests"))))
        results.append(subprocess.check_output([sys.executable, "-c", script], env=env, text=True))
    assert results[0] == results[1]
    assert json.loads(results[0]) == snapshot(make_questions())


@pytest.mark.parametrize("ids", [("TRUE", "FALSE"), tuple("ABCDEFGHIJ")])
def test_option_counts_and_true_false(ids):
    questions = make_questions()[:1]
    questions[0].question.options = [{"id": key, "text": key, "is_correct": index == 0} for index, key in enumerate(ids)]
    assert set(snapshot(questions)["questions"][0]["options_order"]) == set(ids)


def test_saved_snapshot_render_and_original_id_submission():
    questions = make_questions()
    saved = json.loads(json.dumps(snapshot(questions)))
    rendered = render_attempt_questions(saved, list(reversed(questions)))
    assert [item["question_id"] for item in rendered] == [item["question_id"] for item in saved["questions"]]
    for question, row in zip(rendered, saved["questions"]):
        assert [option["id"] for option in question["options"]] == row["options_order"]
        assert all(set(option) == {"id", "text"} for option in question["options"])
        assert "explanation" not in question
    answer = {"question_id": rendered[0]["question_id"], "selected_options": [rendered[0]["options"][0]["id"]]}
    original = copy.deepcopy(answer)
    validate_attempt_answers(saved, [answer])
    assert answer == original
    validate_attempt_answers(saved, [{**answer, "selected_options": []}])
    validate_attempt_answers(saved, [])


@pytest.mark.parametrize("selected", [["Z"], ["A", "A"], [0], "A"])
def test_reject_invalid_option_ids(selected):
    with pytest.raises(ValueError):
        validate_attempt_answers(snapshot(make_questions()), [
            {"question_id": str(UUID(int=1)), "selected_options": selected},
        ])


def test_reject_foreign_or_duplicate_question():
    saved = snapshot(make_questions())
    answer = {"question_id": str(UUID(int=1)), "selected_options": ["A"]}
    for answers in ([answer, answer], [{**answer, "question_id": str(UUID(int=999))}]):
        with pytest.raises(ValueError):
            validate_attempt_answers(saved, answers)


@pytest.mark.parametrize("fault", ["exam", "question", "index", "options", "duplicate"])
def test_reject_invalid_source(fault):
    questions = make_questions()
    if fault == "exam":
        questions[0].exam_id = UUID(int=999)
    elif fault == "question":
        questions[0].question_id = UUID(int=999)
    elif fault == "index":
        questions[0].order_index = questions[1].order_index
    elif fault == "options":
        questions[0].question.options = [{"id": "a"}, {"id": "B"}]
    else:
        questions.append(questions[0])
    with pytest.raises(ValueError):
        snapshot(questions)


def test_empty_exam_and_invalid_attempt():
    assert snapshot([]) == {"version": 1, "questions": []}
    with pytest.raises(ValueError):
        build_attempt_snapshot([], STUDENT, EXAM, 0)


@pytest.mark.parametrize("fault", ["version", "duplicate", "missing", "options"])
def test_reject_invalid_or_stale_snapshot(fault):
    questions = make_questions()
    saved = snapshot(questions)
    if fault == "version":
        saved["version"] = 2
    elif fault == "duplicate":
        saved["questions"].append(saved["questions"][0])
    elif fault == "missing":
        saved["questions"][0]["question_id"] = str(UUID(int=999))
    else:
        saved["questions"][0]["options_order"] = ["A", "Z"]
    with pytest.raises(ValueError):
        render_attempt_questions(saved, questions)
