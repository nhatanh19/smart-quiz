# Issue #6 — Regex Pattern Matching Engine for Questions & Options (WBS 2.1.2)

Branch: `feature/issue-6-regex-parser`  
Module: `module:parser` (Dev 1)  
Priority / Effort: `must-have` (5 Story Points)

---

## 1. Scope & Alignment with Project Docs

Implemented following `docs/DETAILED_GITHUB_ISSUES.md` (Issue #6), `docs/WBS_AND_BACKLOG.md` (WBS 2.1.2), `docs/DATABASE_GUIDE.md` (§3, §4.3, §5.1, §6), `docs/AUTHENTICATION.md`, `docs/ISSUE_4_HANDOFF.md`, `docs/ISSUE_5_HANDOFF.md`, and `TECH_STACK.md` (§6 module ownership).

- **Multi-format Regex Parser (`RegexQuestionParserService`):**
  - **Tiêu đề câu hỏi:** `Câu 1:`, `Câu 01.`, `Câu hỏi 1:`, `Question 1:`, `Q1:`, `Q.1:`, `Bài 1:`, và fallback đánh số `1.`, `1)` kèm kiểm chứng tránh tách nhầm danh sách ý bên trong đề thi.
  - **Phương án lựa chọn (`A`–`J`):** Hỗ trợ `A.`, `A)`, `A:`, `(A)`, chữ thường `a.`, phương án nhiều dòng, nhiều phương án trên cùng dòng (2 hoặc 4 cột), bảng DOCX phân tách bởi `|`, đồng thời chống cắt nhầm chữ viết tắt giữa câu (`Grade A.`, `Vitamin B.`, `C. Ronaldo`).
  - **Nhận diện đáp án đúng:**
    1. Ký hiệu inline: `*A.`, `* A.`, `[x] A.`, `(x) A.`, `✓ A.`, `(Đúng)`, `[Đúng]`, `A. ... *`, hoặc dòng riêng `*a.`.
    2. Định dạng Word (`.docx`) qua `DocxExtractor` + `FileParserService.parse_file_with_hints()`: phát hiện phương án được **gạch chân (`underline`)**, **highlight**, hoặc **tô màu nhấn mạnh đỏ/xanh lá** mà **không** làm thay đổi `raw_text` thuần túy của Issue #5 (`POST /api/v1/parser/upload`).
    3. Dòng đáp án tường minh: `Đáp án: A`, `Đáp án đúng: A, C`, `ĐA: B`, `Answer: B & D`, `Key: AC`, hoặc `Đáp án: Đúng` cho câu Đúng/Sai.
    4. Bảng đáp án cuối đề (`ĐÁP ÁN` / `BẢNG ĐÁP ÁN` / `ANSWER KEY`) ánh xạ theo số thứ tự câu.
  - **Nhận diện loại câu hỏi & lời giải thích:**
    - Tự phân loại `SINGLE_CHOICE`, `MULTIPLE_CHOICE` ($\ge 2$ đáp án đúng), `TRUE_FALSE` (2 phương án `Đúng/Sai` hoặc `True/False`).
    - Hỗ trợ tách lời giải thích/ghi chú nhiều dòng (`Giải thích:`, `Lời giải:`, `Hướng dẫn giải:`, `Ghi chú:`, `Explanation:`, `Note:`).
    - Tự gắn `source_type = "FILE_PARSER"`, `is_valid`, và `warnings` để hỗ trợ chỉnh sửa inline ở **Issue #7**.
- **UI Scope Decision:** Giữ nguyên giao diện `DocumentParserTab.tsx` của Issue #5; toàn bộ bảng duyệt trước và chỉnh sửa câu hỏi thực hiện ở **Issue #7 (`WBS 2.2.1`)**.

---

## 2. API Endpoints & Security Contract

- `POST /api/v1/parser/parse-questions`
  - **Request:** `DirectTextParseRequest` (`raw_text`, `filename?`)
  - **Response:** `APIResponse[ParsedQuestionBatchResult]`
- `POST /api/v1/parser/upload-and-parse`
  - **Request:** `multipart/form-data` (`file` `.pdf` / `.docx` / `.txt` $\le 10\text{MB}$)
  - **Response:** `APIResponse[DocumentQuestionExtractionResult]` (`document`, `questions`, `statistics`, `unmatched_answer_keys`, `warnings`)
- **Security:** Cả 2 endpoint bắt buộc `Depends(require_roles([UserRole.INSTRUCTOR, UserRole.ADMIN]))` (`401` nếu chưa đăng nhập, `403` nếu `STUDENT`) và `Depends(check_origin)` (`403` với `Origin` lạ hoặc `sec-fetch-site: cross-site`).
- Endpoint cũ `GET /api/v1/parser/health` và `POST /api/v1/parser/upload` giữ nguyên hành vi Issue #5.

---

## 3. JSON Output Contract for Issue #7 (`WBS 2.2.1`)

Mỗi phần tử trong `questions` (`ParsedQuestionSchema`) tuân thủ chuẩn lưu bảng `questions`:

```json
{
  "question_number": 1,
  "content": "WBS là viết tắt của cụm từ nào?",
  "question_type": "SINGLE_CHOICE",
  "cognitive_level": "REMEMBER",
  "level": "MEDIUM",
  "options": [
    { "id": "A", "text": "Work Breakdown Structure", "is_correct": true },
    { "id": "B", "text": "Work Budget Schedule", "is_correct": false }
  ],
  "correct_option_ids": ["A"],
  "explanation": "WBS phân rã phạm vi dự án theo sản phẩm bàn giao.",
  "tags": [],
  "source_type": "FILE_PARSER",
  "is_valid": true,
  "warnings": []
}
```

Frontend service `frontend/src/services/parserApi.ts` đã xuất sẵn các hàm `parseQuestionsFromText` và `uploadAndParseDocument` cùng các TypeScript interfaces tương ứng (`ParsedQuestionItem`, `ParsedQuestionBatchResult`, `DocumentQuestionExtractionResult`).

---

## 4. Key Files Changed / Added

- **Backend:**
  - `backend/app/modules/parser/schemas.py`
  - `backend/app/modules/parser/services/file_parser_service.py`
  - `backend/app/modules/parser/services/regex_question_parser.py`
  - `backend/app/modules/parser/services/__init__.py`
  - `backend/app/modules/parser/router.py`
  - `backend/tests/test_regex_question_parser.py`
- **Frontend:**
  - `frontend/src/services/parserApi.ts`
  - `frontend/src/pages/parser/DocumentParserTab.test.tsx`
- **Docs:**
  - `docs/ISSUE_6_HANDOFF.md`

---

## 5. Verification

From repository root:

```powershell
backend/.venv/Scripts/python.exe -m pytest backend/tests -q -p no:cacheprovider
backend/.venv/Scripts/python.exe -m pytest backend/tests/test_regex_question_parser.py -v -p no:cacheprovider
```

- Full backend suite: **222 passed, 4 skipped** (4 PostgreSQL-only tests skip when `AUTH_TEST_DATABASE_URL` is unset).
- Issue #6 suite (`test_regex_question_parser.py`): **11 passed** (covering Tier 1–5 structure matching, inline/multi-column options, `*A.` / `[x]` / `(Đúng)` / DOCX underline & highlight / trailing key table, `>= 90%` benchmark on 20-question `.docx` and `.pdf` sample papers, and RBAC + `check_origin` security).

From `frontend`:

```powershell
npm.cmd run test
npm.cmd run build
```

- Vitest: **6 test files, 64 passed** (including 2 new Issue #6 API helper tests in `DocumentParserTab.test.tsx`).
- Build (`tsc && vite build`): **passed** with 0 errors.
