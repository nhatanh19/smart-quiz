# Issue #34 — Focused exam room

Branch: `feature/issue-34-focused-exam-room`

## Delivered

- Lobby starts/resumes an attempt and opens `/exam/:attemptId` in the isolated, student-only exam layout.
- Question navigation, answered count, single/multiple selection using original option IDs, submit confirmation and review redirect.
- Countdown uses the server-provided absolute `expires_at`; timeout disables answer edits and submits once. Failed requests retain recovery data and allow retry; reconnect triggers another expired submission.
- Local recovery is scoped to student ID and attempt ID. Every answer interaction writes immediately so an immediate reload does not lose the last choice. The persistence effect also uses a 300ms debounce and flushes on pagehide.
- Server answer synchronization is debounced by 300ms and serialized to prevent out-of-order saves. Reconnect retries while the attempt is open.
- Successful submission clears only the current attempt cache. A failed submit checks server status to recover from a response lost after commit.

## API changes

- `GET /api/v1/exam-engine/attempts/{attempt_id}`: owner-only recovery of public questions, deadline, status and saved answers. No correct-answer fields.
- `POST /api/v1/exam-engine/attempts/{attempt_id}/answers`: owner-only, origin-checked save before the deadline, with snapshot/option validation and row locking.
- Submit after the deadline grades only answers already saved on the server, sets `EXPIRED` with `submitted_at = expires_at`, and commits grading atomically. Late payload answers are ignored so the deadline remains authoritative.

## Offline limitation

LocalStorage preserves answers on this browser during outages. To count toward grading, answers must reach the server before `expires_at`. Unsynchronized local answers cannot be accepted after the deadline because the server cannot verify when they were entered. Closing the browser does not run a server scheduler; timeout grading runs when the client submits/reconnects.

## Verification

- Frontend exam tests: 10 passed.
- Backend exam engine and shuffle tests: 44 passed, 1 PostgreSQL-only concurrency test skipped under SQLite.
- Grading and review regression tests: 33 passed.
- Frontend production build passed.

## Follow-up #35

Merge #34 before branching #35 from main. Add focus monitoring, merge blur/visibility events within 500–1000ms, read the threshold from exam.max_tab_violations, and count only TAB_SWITCH/WINDOW_BLUR/DEVTOOLS_SHORTCUT. COPY_PASTE_ATTEMPT is logged without incrementing. At lockout validate/upsert payload answers, set LOCKED_VIOLATION and submitted_at, call grade_attempt, then commit once. Clear the attempt cache and redirect to review after server confirmation.
