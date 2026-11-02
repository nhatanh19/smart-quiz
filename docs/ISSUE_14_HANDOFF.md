# Issue #14 — Auto-Grading Engine Implementation & Integration Handoff

Branch: `feature/issue-14-auto-grading-engine`.
Assignee: Dev 4 (Mai Văn Tỉnh — `@MaiVanTinh17072005`).

---

## 1. Overview & Handoff Alignment with Issue #13

Issue #14 implements the **Instant Multi-Question Type Auto-Grading Engine** adhering strictly to:
- `docs/DEV3_DEV4_WORKING_AGREEMENT.md` (Section 5, Section 7, Section 8)
- `docs/DATABASE_GUIDE.md` (Section 5.3, 5.4, Section 6)
- Contract established in Issue #13 (`docs/ISSUE_13_HANDOFF.md`):
  - **K-01**: `selected_options` contains ORIGINAL option IDs (`"A"`, `"B"`...), not display positions.
  - **K-02**: Every `question_id` must belong to `question_order_snapshot`. Verified independently in `grade_attempt()`.
  - **I-01**: `grade_attempt()` does NOT commit, only `db.flush()`. Caller (Dev 3 in `submit`) commits the whole transaction.
  - **I-04**: Endpoint `POST /api/v1/tutor-analytics/grade/{attempt_id}?force=false` allows instructors/admins to re-grade.

---

## 2. Core Service Signature

```python
# backend/app/modules/tutor_analytics/services/grading_service.py
@dataclass
class GradingResult:
    attempt_id: uuid.UUID
    score: float
    correct_count: int
    total_questions: int
    answers: list[dict]          # [{question_id, is_correct, points_awarded}]
    time_spent_seconds: int
    already_graded: bool = False

def grade_attempt(
    db: Session,
    attempt_id: uuid.UUID,
    *,
    force: bool = False,
) -> GradingResult:
    """Synchronous auto-grading engine. Flushes changes to DB (NO COMMIT)."""
```

---

## 3. Grading Algorithm & Formula

- **`SINGLE_CHOICE`**:
  - `ratio = 1.0` if $S == C$ and $|S| == 1$, else $0.0$.
  - `is_correct = (S == C and len(S) == 1)`.
- **`TRUE_FALSE`**:
  - Validates 2 options and 1 correct answer.
  - `ratio = 1.0` if $S == C$ and $|S| == 1$, else $0.0$.
- **`MULTIPLE_CHOICE`**:
  - Partial credit formula:
    $$\text{ratio} = \text{clamp}\left(\frac{|S \cap C| - |S \setminus C|}{|C|}, 0, 1\right)$$
  - `is_correct = (S == C)`.
- **Unanswered / Empty $S = []$**:
  - `ratio = 0.0`, `is_correct = False`.
- **Points Awarded**:
  - `points_awarded = round(exam_questions.points * ratio, 2)`
- **Total Score (10-point scale)**:
  - $\text{score} = \text{clamp}\left(\text{round}\left(\frac{\sum \text{points\_awarded}}{\sum \text{exam\_questions.points}} \times 10, 2\right), 0, 10\right)$
  - If $\sum \text{exam\_questions.points} \le 0 \implies \text{score} = 0.0$.
- **Time Spent**:
  - $\text{time\_spent\_seconds} = \max(0, \text{int}((\text{submitted\_at} - \text{started\_at}).\text{total\_seconds}()))$.

---

## 4. Edge Cases E1 to E10 Verification

| # | Edge Case | Expected Behavior | Implementation & Test |
| :---: | :--- | :--- | :--- |
| **E1** | `attempt_id` does not exist | Raise `NotFoundError` (HTTP 404) | Handled & verified in `test_e1_attempt_not_found` |
| **E2** | Already `SUBMITTED`, `force=False` | Return cached result, `already_graded=True`, no DB write | Handled & verified in `test_e2_already_submitted_without_force` |
| **E3** | `LOCKED_VIOLATION` / `EXPIRED` | Grade normally; preserve status, populate `submitted_at` | Handled & verified in `test_e3_locked_violation_or_expired_grading` |
| **E4** | `question_id` not in snapshot (K-02) | Raise `SnapshotMismatchError` (HTTP 400) | Handled & verified in `test_e4_question_not_in_snapshot_k02` |
| **E5** | `selected_options` has foreign ID | Treated as wrong (`ratio=0`), warning logged, no crash | Handled & verified in `test_e5_selected_options_contain_invalid_option_id` |
| **E6** | Duplicate IDs in `selected_options` | Deduplicated before grading | Handled & verified in `test_e6_duplicate_selected_options_deduped` |
| **E7** | Question has no `AttemptAnswer` | 0 points awarded, counted in `total_questions`, answer created | Handled & verified in `test_e7_question_without_attempt_answer_record` |
| **E8** | 0 questions / total points = 0 | `score = 0.0`, safe from ZeroDivisionError | Handled & verified in `test_e8_zero_questions_or_zero_points` |
| **E9** | Score rounding boundary | Clamped to `[0.0, 10.0]` matching DB constraint | Handled & verified in `test_e9_score_clamping` |
| **E10** | Consecutive `grade` calls | Idempotent; no duplicate scores or answers | Handled & verified in `test_e10_idempotent_consecutive_calls` |

---

## 5. Performance & DoD Compliance

- **SLA < 300ms**: 1 query with `joinedload(ExamQuestion.question)`, 1 query for `AttemptAnswer`. In-memory grading for 50 questions executes in **< 15ms** (verified in `test_grading_performance_under_300ms`).
- **Database constraints**: Complies with `closed_at_matches_status`, `score_range`, and JSONB schema.
- **Test suite**:
  - `backend/tests/test_grading.py`: 18 tests covering all requirements, formulas, edge cases, role permissions, and performance SLA.
  - Total backend suite: **57 passed**, 3 skipped (requiring live Postgres).
  - Frontend: `npm run build` passed with zero errors.
