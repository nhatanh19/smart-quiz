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

Access tokens expire after 15 minutes; refresh tokens after 7 days by default. JWTs have distinct access/refresh purposes and user UUID subjects. JavaScript receives public user information, never raw tokens. Cookies use HttpOnly and SameSite=Lax. Axios includes credentials and retries protected requests once after refreshing an expired access token. Protected routes query `/me` rather than trusting browser storage.

Use the same site for frontend and API (localhost with separate ports works). Set a strong SECRET_KEY, COOKIE_SECURE=true and HTTPS in production. BACKEND_CORS_ORIGINS must contain the exact frontend origin. Mutating auth endpoints reject unapproved origins and cross-site fetches. Cross-site hosting is not supported by this cookie configuration.

Refresh tokens are stateless. A renewed token does not revoke the previous one; logout clears this browser's cookies but does not revoke copied tokens. Persisted refresh sessions and one-time rotation are a future extension.

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

Verified: 11 API tests pass and frontend production build passes. API tests create the actual User table in isolated in-memory SQLite and exercise real bcrypt and JWT signatures. They cover password persistence, duplicate email, selected STUDENT/INSTRUCTOR role persistence through login, invalid role rejection, credentials, validation, cookie flags, profile, refresh, logout, expired tokens and token purpose. PostgreSQL integration and browser interaction have not been verified.

Manual browser check: open `/register`, create accounts with each account type (Học sinh and Giáo viên), follow the success message to `/login`, check invalid credentials, sign in, reload the workspace and sign out. Cookies should be HttpOnly in browser developer tools and localStorage should contain no authentication tokens.

Per project workflow, mark the issue Done only after the remaining manual validation and PR approval/merge.
