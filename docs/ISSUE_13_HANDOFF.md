# Issue #13 — handoff to Dev 4

Branch: `feature/issue-13-seed-shuffling`.
Contract-first commit (G1.2): `ecee56f`.

## Contract

- `build_attempt_snapshot()` implements DATABASE_GUIDE section 5.3, version 1.
- SHA-256 seed includes student ID, exam ID and attempt number. Fisher-Yates
  uses independent local RNGs for question ordering and each question's options.
- K-01: `selected_options` contains ORIGINAL option IDs, never display labels or
  indexes. Render labels by position but submit the returned option `id`.
- K-02: call `validate_attempt_answers(snapshot, answers)` before any DB writes;
  Dev 4 must independently check snapshot membership during grading.
- `render_attempt_questions()` returns only public fields, in snapshot order.
- Different seeds can produce identical permutations. Independent shuffling
  does not mathematically guarantee different permutations for every student.

## Integration with #12 and #14

1. #12 loads `ExamQuestion.question` eagerly, ordered by `order_index`.
2. Pass the authenticated student ID, exam ID, server-assigned attempt number,
   and both exam shuffle flags to `build_attempt_snapshot()`.
3. Save the dict in `ExamAttempt.question_order_snapshot` in the attempt-creation
   transaction. This service does not read/write DB or create attempts.
4. Resume uses the SAVED snapshot, not a regenerated one. Freeze source question
   content/options once attempts exist (database specification section 8).
5. Render with `render_attempt_questions(saved_snapshot, exam_questions)`.
6. Submit validates ownership/time/state and typed request data, calls
   `validate_attempt_answers()`, saves original IDs to `AttemptAnswer`, flushes,
   calls Dev 4's `grade_attempt()` and commits once. Map validation ValueError to
   HTTP 400; do not expose a success response for rejected answers.

Start/resume persistence and submit HTTP wiring remain integration work for
#12/Dev 3. Grading remains #14/Dev 4. No schema change is needed.

## Reproducible sample

Test fixture: student UUID(int=200), exam UUID(int=100), attempt 1, question
UUID(int=1) and UUID(int=2), original option IDs A/B/C/D, both flags enabled:

```json
{"version":1,"questions":[
  {"question_id":"00000000-0000-0000-0000-000000000002","options_order":["A","B","D","C"]},
  {"question_id":"00000000-0000-0000-0000-000000000001","options_order":["C","B","D","A"]}
]}
```

## Verification and Gate G1

- G1.3–G1.5: covered in `backend/tests/test_exam_shuffle.py`, including two
  independent Python processes with different PYTHONHASHSEED values.
- G1.6: K-01 is confirmed above and exercised by render/answer validation tests.
- G1.1: copy the sample and contract to issue #13; no GitHub comment has been sent.
- Focused tests: `backend/.venv/Scripts/python.exe -m pytest backend/tests/test_exam_shuffle.py -q -p no:cacheprovider`
  — 25 passed.
- Backend suite: `backend/.venv/Scripts/python.exe -m pytest backend/tests -q -p no:cacheprovider`
  — 39 passed, 3 PostgreSQL tests skipped without AUTH_TEST_DATABASE_URL.
- Frontend: `cd frontend; npm.cmd run build` — passed.

Publish the implementation commit SHA with the handoff and tag
`@MaiVanTinh17072005` and `@nhatanh19` when authorized to comment on GitHub.
