# Issue #5 — File Upload Pipeline & Raw Text Extraction (WBS 2.1.1)

Branch: `feature/issue-5-file-upload`  
Module: `module:parser` (Dev 1)  
Priority / Effort: `must-have` (3 Story Points)

---

## 1. Scope & Alignment with Project Docs

Implemented following `docs/DETAILED_GITHUB_ISSUES.md` (Issue #5), `docs/WBS_AND_BACKLOG.md` (WBS 2.1.1), `TECH_STACK.md` (§3 locked-in Python stack: FastAPI, `python-multipart`, `PyMuPDF`, `python-docx`), `docs/AUTHENTICATION.md`, and `docs/ISSUE_4_HANDOFF.md`.

- **Supported formats:** `.pdf`, `.docx`, `.txt` (case-insensitive extension validation, double-extension rejection such as `.pdf.exe`, missing-extension rejection).
- **Size boundary:** Up to **10 MB** (`10,485,760` bytes) via bounded 1 MB chunked stream reading (`LIMIT_READ_BYTES = 10MB + 1`). Empty (`0` bytes) and oversized files are rejected with HTTP `400`.
- **Extraction & UTF-8 preservation:**
  - `PdfExtractor` (`pymupdf`): Extracts native text per page, rejects encrypted/password-protected PDFs, blank PDFs, and malformed streams. Returns accurate `page_count`.
  - `DocxExtractor` (`python-docx`): Extracts paragraphs and table rows (` | ` separated) with merged-cell deduplication; rejects corrupted ZIP/DOCX packages and empty documents.
  - `TxtExtractor`: Decodes `utf-8` / `utf-8-sig` (strips UTF-8 BOM), rejects null-byte binary payloads and invalid encodings, and rejects whitespace-only files.
  - Computes `character_count` and `word_count` and preserves 100% Vietnamese diacritics.
- **Out of scope (deferred to subsequent issues):** Regex question/option splitting (Issue #6) and inline preview/edit table (Issue #7).

---

## 2. Security & Auth Integration

- `POST /api/v1/parser/upload` enforces:
  - `Depends(require_roles([UserRole.INSTRUCTOR, UserRole.ADMIN]))` (`401` unauthenticated, `403` `STUDENT`).
  - `Depends(check_origin)` rejecting disallowed `Origin` headers and `sec-fetch-site: cross-site` requests (`403`).
- `GET /api/v1/parser/health` remains public.
- Frontend service `frontend/src/services/parserApi.ts` uses the shared `apiClient` (`withCredentials: true` HttpOnly cookies + automatic `/auth/refresh` retry) without reading `localStorage` tokens.

---

## 3. Key Files

- Backend:
  - `backend/app/modules/parser/router.py`
  - `backend/app/modules/parser/schemas.py`
  - `backend/app/modules/parser/exceptions.py`
  - `backend/app/modules/parser/services/__init__.py`
  - `backend/app/modules/parser/services/file_parser_service.py`
  - `backend/tests/test_file_parser.py`
  - `backend/tests/test_auth.py` (passes minimal file payload for `/api/v1/parser/upload` in `test_management_api_role_matrix`)
- Frontend:
  - `frontend/src/services/parserApi.ts`
  - `frontend/src/pages/parser/DocumentParserTab.tsx`
  - `frontend/src/pages/parser/ParserPlaceholder.tsx` (two-tab layout: Document Parser & Question Bank)
  - `frontend/src/pages/parser/DocumentParserTab.test.tsx`

---

## 4. Verification

From repository root:

```powershell
backend/.venv/Scripts/python.exe -m pytest backend/tests -q -p no:cacheprovider
```

- Result: **196 passed, 4 skipped** (4 PostgreSQL-only tests skip when `AUTH_TEST_DATABASE_URL` is unset), including 46 parser tests covering Tier 1–4 extraction/boundary/real-world cases and Tier 5 RBAC + origin security.

From `frontend`:

```powershell
npm.cmd run test
npm.cmd run build
```

- Vitest: **5 test files, 40 passed** (including 5 new tests in `DocumentParserTab.test.tsx`).
- Build (`tsc && vite build`): **passed** with 0 errors.
