# Issue #7 — Question Extraction Preview & Inline Editing Table (WBS 2.2.1)

Branch: `feature/issue-7-preview-ui`  
Module: `module:parser` (Dev 1)  
Priority / Effort: `must-have` (3 Story Points)

---

## 1. Scope & Implemented Behavior

Implemented in alignment with `docs/ISSUE_5_HANDOFF.md`, `docs/ISSUE_6_HANDOFF.md`, `docs/DATABASE_GUIDE.md`, and `docs/AUTHENTICATION.md`:

- **Single-step Upload & Parse Flow (`DocumentParserTab.tsx`):**
  - Uploading `.pdf`, `.docx`, or `.txt` calls `POST /api/v1/parser/upload-and-parse` via `uploadAndParseDocument()` (HttpOnly cookie `apiClient`, preserving Issue #5 file validation, progress bar, metadata counters, copy, and `.txt` download).
  - Success view provides a dual view switcher:
    - **Xem trước & Sửa câu hỏi (`N`)** (auto-opened whenever `questions.length > 0`).
    - **Văn bản thô đã bóc tách** (with **"Phân tích lại bằng Regex"** calling `POST /api/v1/parser/parse-questions`).
- **Inline Question Preview, Validation & Editing (`ParsedQuestionPreviewPanel.tsx` & `parsedQuestionUtils.ts`):**
  - Displays live KPIs (`Tổng câu nhận diện`, `Hợp lệ`, `Cần kiểm tra`, `Có giải thích`, `Đã lưu ngân hàng`) and any document-level `warnings` / `unmatched_answer_keys`.
  - Supports filtering (`Tất cả`, `Hợp lệ`, `Cần kiểm tra`), keyword search, and bulk selection of valid questions.
  - Inline per-card editing with real-time client re-validation (`revalidateParsedQuestion`):
    - Question stem (`<textarea>`), question type (`SINGLE_CHOICE`, `MULTIPLE_CHOICE`, `TRUE_FALSE`), Bloom cognitive level, and difficulty level.
    - Answer options `A–J`: 1-click radio/checkbox answer switching, inline option text editing, add/remove options (`2–10`) with automatic re-indexing.
    - Expandable `Giải thích & Tags` editor.
    - Smooth question deletion with multi-step **"Hoàn tác xóa"** undo history, plus **"+ Thêm câu hỏi"** manual append.
- **Save Reviewed Questions to Question Bank (`source_type = "FILE_PARSER"`):**
  - `backend/app/schemas/common.py`: Added backward-compatible optional `source_type: QuestionSource = QuestionSource.MANUAL` to `QuestionCreateSchema`.
  - `frontend/src/services/questionBankApi.ts`: Extended `QuestionPayload` with optional `source_type?: QuestionSource`.
  - Destination selector loads `subjects` and `categories` via `apiClient` (compatible with both subject-linked and legacy categories), saves selected valid questions sequentially with live progress, marks saved cards in-place, and triggers `onQuestionsSaved` in `ParserPlaceholder.tsx`.

---

## 2. Key Files Changed / Added

- **Backend:**
  - `backend/app/schemas/common.py` (`QuestionCreateSchema.source_type`)
  - `backend/tests/test_question_bank_api.py`
- **Frontend:**
  - `frontend/src/services/questionBankApi.ts`
  - `frontend/src/pages/parser/parsedQuestionUtils.ts` *(new)*
  - `frontend/src/pages/parser/ParsedQuestionPreviewPanel.tsx` *(new)*
  - `frontend/src/pages/parser/DocumentParserTab.tsx`
  - `frontend/src/pages/parser/ParserPlaceholder.tsx`
  - `frontend/src/pages/parser/DocumentParserTab.test.tsx`
- **Docs:**
  - `docs/ISSUE_7_HANDOFF.md`

---

## 3. Verification Results

From repository root:

```powershell
backend/.venv/Scripts/python.exe -m pytest backend/tests/test_question_bank_api.py -v -p no:cacheprovider
backend/.venv/Scripts/python.exe -m pytest backend/tests -q -p no:cacheprovider
```

- `test_question_bank_api.py`: **10 passed, 2 warnings** (including `test_create_question_preserves_optional_file_parser_source_type`).
- Full backend suite: **223 passed, 4 skipped, 19 warnings** (4 PostgreSQL-only tests skip when `AUTH_TEST_DATABASE_URL` is unset).

From `frontend`:

```powershell
npm.cmd run test
npm.cmd run build
```

- Vitest: **6 test files, 65 passed** (including `DocumentParserTab.test.tsx` with 8 tests covering Issue #5, #6, and #7 inline editing + undo + save-to-bank).
- Build (`tsc && vite build`): **passed** (`dist/assets/index-A0PABjBC.js 376.95 kB`).

E2E `/browser` (`http://localhost:5176/instructor/parser` backed by `http://localhost:8011`):

- Uploaded `mau_de_issue7.docx` (`4` questions detected: `SINGLE_CHOICE` DOCX underline, `MULTIPLE_CHOICE` `*B`/`*D`, missing answer warning on Q3, draft Q4).
- Fixed Q3 missing answer inline (warning cleared to `Hợp lệ`), edited Q1 stem inline, deleted + undid + re-deleted Q4, switched to raw text view and back, and saved the 3 edited questions to category `Quản trị Dự án Phần mềm` (`POST /api/v1/ai-generator/question-bank/questions` HTTP `200/201`, verified persisted in PostgreSQL with `source_type = FILE_PARSER`).
