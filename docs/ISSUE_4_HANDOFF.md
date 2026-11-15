# Issue #4 — RBAC and User Profile (WBS 1.2.2)

## Implemented behavior

- `/profile` is available to every authenticated role. It displays an initials avatar, full name, email, and Vietnamese role label alongside the role code. No schema migration or avatar upload is required.
- `/instructor/*` requires INSTRUCTOR or ADMIN, including unknown nested paths. `/instructor/parser`, `/instructor/ai-generator`, and `/instructor/analytics` reuse existing module screens.
- Legacy `/parser`, `/ai-generator`, and `/analytics` paths enforce the same roles before redirecting. STUDENT cannot bypass the guard through an old URL.
- `/admin/*` permits ADMIN only. No admin management screen or exam creation screen is implemented by this issue.
- `/` sends STUDENT to `/profile` and INSTRUCTOR/ADMIN to `/instructor/parser`. Management links are hidden for students. Authentication still comes from the shared AuthProvider and `/auth/me`.
- Protected routes show a loading state until the session is checked, redirect anonymous users to `/login`, and render a 403 view for the wrong role.
- Logout clears the two HttpOnly cookies through the existing endpoint, clears AuthProvider state, and navigates to `/login` with history replacement. Failed logout retains the session and displays an error. Concurrent logout requests share one request; pending refresh finishes before cookie deletion, and new automatic refresh is suppressed during logout.

## API authorization

Use FastAPI `Depends(get_current_user)` / `Depends(require_roles(...))`; the database user role is authoritative, not the JWT role claim.

| API group | Access |
| --- | --- |
| `/auth/me` | Any active authenticated user; public user fields only |
| Parser upload, AI matrix/context generation | INSTRUCTOR / ADMIN |
| Question Bank and parser compatibility aliases | Existing INSTRUCTOR / ADMIN and ownership checks retained |
| Exam start, submit, violation placeholders | STUDENT; persistence and attempt ownership remain with the exam implementation |
| Grade/regrade | ADMIN or instructor owning the attempt's exam |
| Review / attempt-backed AI Tutor | ADMIN, owning instructor, or owning student after leaving IN_PROGRESS |
| AI Tutor question IDs | Attempt-backed IDs must belong to the saved snapshot; standalone question IDs require ADMIN or their creating instructor |
| AI Tutor with supplied text/options only | Any authenticated user; does not access stored question/attempt data |
| Student analytics placeholder | The same user or ADMIN |
| Exam analytics placeholder | ADMIN or owning instructor |
| Health checks | Public |

API returns 401 for missing/invalid authentication and 403 for insufficient permissions. Existing resource-not-found responses remain 404.

## Scope and session limitations

Logout follows the existing Issue #3 contract: it deletes this browser's cookies. Stateless JWT copies are **not revoked server-side**. Refresh-session persistence, reuse detection, and immediate invalidation of copied access/refresh tokens require a separate session-storage change and migration. No tokens are placed in localStorage.

Issue #12 must add real instructor exam management pages/APIs under the protected group and enforce exam ownership. Existing exam start/submit/violation handlers remain placeholders; their business behavior is not delivered by Issue #4. Analytics placeholders remain placeholders as well.

Frontend `allowedRoles` improves navigation; API dependencies enforce actual access control. Module route changes in parser, AI generator, and tutor analytics are limited to authorization and should be included in the relevant owners' review.

## Validation

From repository root:

```powershell
backend/.venv/Scripts/python.exe -m pytest backend/tests -q -p no:cacheprovider
```

Result: **97 passed, 3 skipped**. PostgreSQL tests skip without AUTH_TEST_DATABASE_URL.

Verified on **2026-11-07**, using local PostgreSQL **17.11**: **100 passed, 0 skipped** (18.35s). Set AUTH_TEST_DATABASE_URL in the process environment before running the command above. Authentication/RBAC, profile API, logout, grading/ownership, and migration/native enum/JSONB checks ran against a migrated temporary PostgreSQL database. Question Bank's existing tests still use their fake session; shuffle and standalone tutor service tests do not require a database. Grading fixtures now reuse the temporary PostgreSQL engine when configured and retain SQLite as their default fallback.

The real-database check found the existing `ix_categories_subject_id` index declared in migration but missing from ORM metadata. The Category model now declares the same index; no new migration or application-database change was needed. Teardown was verified: zero `smart_quiz_auth_test_*` databases remained.

From `frontend`:

```powershell
npm.cmd run test
npm.cmd run build
```

Frontend: **22 tests passed**, covering direct/legacy routes, role-based home redirects, profile fields/avatar, logout success/failure, and simultaneous refresh/logout. These are jsdom component/client tests, not real-browser end-to-end tests.

Manual review before closing the issue: log in with each role, open `/profile`, reload, try instructor URLs directly and through old aliases, sign out, then use Back/reload. Verify HttpOnly cookies disappear and protected data is inaccessible. PR review/merge and real-browser validation are still required for project-level Done.
