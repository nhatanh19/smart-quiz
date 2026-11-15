# Issue #12 — Exam creation, lobby, start/resume and submit

## Confirmed scope and references

Implemented following the lead's scope clarification: backend includes exam management, code/PIN entry, A1 start/resume and A2 submit -> grade. Frontend includes creation, lobby/start and a minimal question/submit screen to test the complete flow. Full focus-room UX, live countdown, question navigation, auto-submit and localStorage recovery remain Sprint 2.

References: DETAILED_GITHUB_ISSUES issue #12 / WBS 4.1.1, DEV3_DEV4_WORKING_AGREEMENT sections 5.3 and 8, ISSUE_13_HANDOFF, ISSUE_14_HANDOFF, database specification section 8.

## Backend contract

Prefix: `/api/v1/exam-engine`. Responses use the shared `{success, message, data}` envelope. All resource IDs are UUIDs.

| Method/path | Role | Behavior |
| --- | --- | --- |
| POST `/exams` | INSTRUCTOR / ADMIN | Create exam and selected question associations atomically; returns generated code |
| GET `/exams?skip=0&limit=50` | INSTRUCTOR / ADMIN | Own exams; ADMIN sees all; limit up to 100 |
| GET `/exams/{id}` | Owner / ADMIN | Configuration and selected question IDs/points |
| PUT `/exams/{id}` | Owner / ADMIN | Full replacement, including PIN and publication flag; blocked once attempts exist |
| POST `/exams/join` | STUDENT | `{exam_code, pin}`; validates entry and sets scoped HttpOnly entry cookie |
| GET `/exams/{id}/lobby` | STUDENT + entry grant | Safe exam metadata, no questions or answer keys |
| POST `/exams/{id}/start` | STUDENT + entry grant | Body-free A1: starts or resumes, returns attempt ID, expiry and public questions |
| POST `/attempts/{id}/submit` | Owning STUDENT | A2: `{answers: [{question_id, selected_options}]}`; validates, saves and grades atomically |

Create/update payload:

```json
{
  "title": "Ca thi mẫu", "description": "Hướng dẫn",
  "start_time": "2026-11-09T08:00:00+07:00", "end_time": "2026-11-09T10:00:00+07:00",
  "duration_minutes": 30, "pin": "123456", "max_attempts": 1,
  "shuffle_questions": true, "shuffle_options": true, "is_published": true,
  "questions": [{"question_id": "<uuid>", "points": 1}]
}
```

Durations/points must be positive, attempts >= 1, end > start, timezone required. Select 1–500 distinct questions. Instructor can use own questions; ADMIN can use all. Exam creator comes from the authenticated user, never client-supplied ownership. Eight-character random room codes have a database unique constraint and bounded collision retry. PIN is bcrypt hashed and is never included in a response.

## Implementation decisions

These details fill the existing schema/API contract; they are not additional lead-approved acceptance criteria:

- PIN remains optional, matching nullable `access_password_hash` and the documented PIN-free demo exam. No six-digit-only restriction was introduced. Empty PIN means no PIN; bcrypt input is limited to 72 UTF-8 bytes.
- The form exposes `is_published` (checked by default); API defaults to false. Unpublished/closed exams cannot be joined. Before opening time, entry to the lobby is allowed but start is rejected.
- Join does not create an attempt or consume a turn. Its signed HttpOnly cookie is bound to user, exam, configuration version and closing time, scoped to the exam-engine API. Direct start/lobby access without it fails. Mutating endpoints reuse the project's same-site origin check. Entry grants are stateless, with the same copied-token limitation as current auth.
- `expires_at = min(started_at + duration_minutes, end_time)`. Time is checked server-side; the minimal frontend does not auto-submit. Expired submissions are rejected with 409 and the attempt is marked EXPIRED with submitted_at set to its deadline. No new answers are accepted after expiry.
- Resume preserves the existing unexpired IN_PROGRESS attempt and saved snapshot. An expired attempt consumes its turn; a new one is possible only while the exam is open and attempts remain.
- Exam-row locks serialize start/configuration changes; attempt-row locks serialize submit. PostgreSQL unique constraints additionally protect attempt numbering and the single active attempt rule.
- Question rows are locked while starting and editing. Once any exam containing a question has attempts, Question Bank edits are blocked to preserve snapshot/grading consistency. Deletion remains protected by existing foreign keys. Exam replacement is blocked after attempts exist.
- A2 validates K-02 before writes, stores original option IDs (K-01), flushes, calls `grade_attempt()` directly and commits once (I-01). Exceptions roll back answers and grading together. A repeated submission returns 409 rather than modifying the first result.
- No new migration. SQLite's model index now includes its equivalent partial predicate so local tests permit subsequent attempts just as PostgreSQL does.
- Anti-cheat is not implemented here; its endpoint returns 501 rather than reporting fabricated persistence.

## Frontend

- `/instructor/exams` and `/instructor/exams/new`: creation form with question search/pagination, selection, dates, duration, optional PIN, attempt limit, shuffle and publication controls. Lists recent exams/codes. Each selected question defaults to one point; API supports custom positive weights.
- `/exam/join`: student code/PIN form.
- `/exam/lobby/:examId`: protected lobby, start/resume, minimal choices and submit. The backend returns only `{id,text}` options. Selected answers use original IDs. Successful submit opens `/review/:attemptId` from #15.
- The form converts local datetime input to an ISO timestamp. API responses normalize dates to UTC; rendering uses local time.
- Question Bank client now uses shared `apiClient`/HttpOnly cookies, removing its stale localStorage token reader. Role-aware navigation reuses #4.
- Unsaved choices are intentionally in memory only. Reload requires start/resume and does not restore unsubmitted choices; the page states this. Sprint 2 handles caching and full exam UX.

## Validation

Backend suite with `AUTH_TEST_DATABASE_URL` set: **126 passed**, including 19 new exam cases. Auth, exam integration, grading and migration checks use a migrated temporary PostgreSQL database; existing review tests retain SQLite and Question Bank tests retain their fake session. No application data is migrated or seeded by these tests.

Covered: create and atomic rejection, ownership, PIN hashing and bypass prevention, same-site origin rejection, schedule and limits, stable resume, no answer leakage, question/exam freeze, snapshot/option validation, grading rollback, optional PIN, collision retry, and genuinely concurrent start/submit on independent PostgreSQL connections.

Frontend: **30 tests passed**, including five new page-flow tests. Route tests now mock ReviewExamView to avoid unrelated real network requests. Production build passes. Browser E2E remains a separate manual check.

```powershell
# From backend, with AUTH_TEST_DATABASE_URL supplied in the environment:
.venv/Scripts/python.exe -m pytest tests -q -p no:cacheprovider
# From frontend:
npm.cmd run test
npm.cmd run build
```

Manual review: instructor selects questions and creates/publishes a ca thi; student enters code/PIN, starts, reloads/resumes, answers and submits; review displays the persisted result. Verify wrong PIN, direct lobby/start bypass, wrong owner, future/closed schedule and repeat submit are rejected.
