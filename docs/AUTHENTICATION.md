# Authentication — Issue #3 / WBS 1.2.1

## Routes and API

Frontend: `/register`, `/login`. Legacy `/auth/register` and `/auth/login` redirect to these routes.

API prefix: `/api/v1/auth`.

| Endpoint | Request | Result |
| --- | --- | --- |
| POST /register | JSON: email, full_name, password, role (optional) | 201: public user; bcrypt hash persisted; selected STUDENT or INSTRUCTOR role |
| POST /login | JSON: email, password | 200: public user + access/refresh HttpOnly cookies |
| GET /me | Access cookie or access Bearer JWT | Current active user |
| POST /refresh | Refresh cookie | New access/refresh cookies |
| POST /logout | No body | Clears both cookies in this browser |

Passwords require at least 8 characters and at most 72 UTF-8 bytes (bcrypt limit). Email is trimmed and lowercased; the database unique constraint also handles concurrent duplicate registration. The registration form offers Học sinh (STUDENT) and Giáo viên (INSTRUCTOR). Public registration accepts only these roles, defaults to STUDENT when omitted, and rejects ADMIN or other values. The selected role is saved in the existing users.role column; no database migration is needed.

Errors: 409 for duplicate email, 401 with `Email hoặc mật khẩu không đúng.` for incorrect credentials, 422 for invalid input. The frontend displays Vietnamese messages, validates password confirmation, disables the form while submitting and handles connection errors.

## Session storage

Access tokens expire after 15 minutes; refresh tokens after 7 days by default. JWTs have distinct access/refresh purposes and user UUID subjects. JavaScript receives public user information, never raw tokens. Cookies use HttpOnly and SameSite=Lax. Axios includes credentials and retries protected requests once after refreshing an expired access token. A shared AuthProvider loads `/me` when a protected route first mounts, deduplicates pending checks, and shares the user with the layout. Login updates that state directly; logout clears it without another `/me` or refresh request. Public login/register pages do not initiate session checks. A fresh visit to a protected page without valid cookies can still produce `/me` and `/refresh` 401 responses during session recovery.

Use the same site for frontend and API (localhost with separate ports works). Set a strong SECRET_KEY, COOKIE_SECURE=true and HTTPS in production. BACKEND_CORS_ORIGINS must contain the frontend origin; surrounding whitespace and trailing slashes in configuration are removed for both CORS and auth checks. Mutating auth endpoints reject unapproved origins and cross-site fetches. Cross-site hosting is not supported by this cookie configuration.

Refresh tokens are stateless. A renewed token does not revoke the previous one; logout clears this browser's cookies but does not revoke copied tokens. Persisted refresh sessions and one-time rotation are a future extension.

## Scope and follow-up work

Authentication, session recovery, and STUDENT/INSTRUCTOR role selection and persistence are implemented. Issue #4 adds role-protected frontend routes, a read-only `/profile`, and business API authorization. See [ISSUE_4_HANDOFF.md](./ISSUE_4_HANDOFF.md) for the access matrix, scope, and validation.

Follow-up backlog:
- Add login rate limits by IP and normalized email with temporary throttling.
- Persist refresh sessions, rotate tokens once, detect reuse, and revoke sessions on logout.
- Run the optional PostgreSQL migration, authentication, native enum, and JSONB tests in CI. These tests now run locally with AUTH_TEST_DATABASE_URL; the repository still needs a CI workflow and PostgreSQL service.

Issue #3 delivered registration/login and shared cookie-based auth state. Issue #4 builds on these helpers rather than introducing a second authentication mechanism.

## Validation

From the repository root:

```powershell
backend/.venv/Scripts/python.exe -m pip install -r backend/requirements-dev.txt
backend/.venv/Scripts/python.exe -m pytest backend/tests -q -p no:cacheprovider
```

From `frontend`:

```powershell
npm run build
npm run dev
```

API tests exercise real bcrypt and JWT signatures against isolated in-memory SQLite by default, or a migrated temporary PostgreSQL database when configured below. They cover password persistence, duplicate email, selected STUDENT/INSTRUCTOR role persistence through login, invalid role rejection, credentials, validation, cookie flags, current-user data, refresh, logout, expired tokens, token purpose, and origin configuration normalization. Browser interaction requires separate validation.

### Real PostgreSQL validation

From `backend`, set `AUTH_TEST_DATABASE_URL` to a PostgreSQL connection URL using a login with `CREATEDB` permission, then run:

```powershell
# Set AUTH_TEST_DATABASE_URL in the environment before this command.
.venv/Scripts/python.exe -m pytest tests -q -p no:cacheprovider
```

The suite creates a unique `smart_quiz_auth_test_<uuid>` database on that server, applies the actual Alembic migration, and drops only that temporary database in teardown. It never migrates or changes data in the database named by the connection URL. Each test uses a transaction that rolls back even when the application commits. Without AUTH_TEST_DATABASE_URL, auth tests use SQLite and PostgreSQL smoke tests skip.

Verified on 2026-10-29: **17 passed on PostgreSQL 17.11**, including all 14 auth cases and 3 PostgreSQL smoke tests. Smoke tests check migration/ORM parity, native enum rejection, UUID values, JSONB round trips, and database constraints. The test run used SQLAlchemy 2.0.55 built without its optional C extensions in a separate local test runtime because Windows Application Control blocked the installed SQLAlchemy DLL. Browser validation and CI remain separate follow-up work.

Manual browser check: open `/register`, create accounts with each account type (Học sinh and Giáo viên), follow the success message to `/login`, check invalid credentials, sign in, reload the workspace and sign out. Cookies should be HttpOnly in browser developer tools and localStorage should contain no authentication tokens.

Per project workflow, mark the issue Done only after the remaining manual validation and PR approval/merge.
